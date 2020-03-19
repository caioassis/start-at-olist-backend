# Notas gerais

## Faltam algumas coisas na documentação do projeto

- Como configura (.env)?
- Qual banco de dados usa? (vimos que tem diferenças no projeto)

Faltaram essas informações no projeto, e isso é bem importante.

## Documentação da api

- O GET de bills não especifica quais parâmetros devem ser passados
- O POST de end não especifica payload/formato dos dados
- O POST de start não especifica payload/formato dos dados

Nenhum dos 3 acima explica também pra que serve os endpoints. Fora que ficou o nome de `Library API Project` no começo da doc ;)

## Falta de paginação nos endpoints de lista (bills)

É desejado sempre que tenhamos paginação nos endpoints de listagem, isso faz com que a gente não exploda o banco com 1 request e também ajuda a limitar a quantidade de dados devolvida pela api.

## Falta versionamento da api / nomenclatura

Não temos versionamento da api em nenhum endpoint, o mais correto seria:

```
POST /v1/call-records/finished/
GET /v1/call-records/bills/
```

Perceba também que os nomes call_records (com underline) não são muito convencionais em REST, geralmente se temos dois nomes eles são separados pelo uso do hífen (-).

Tem algumas referências interessantes neste link [1], inclusive temos o livro citado na nossa conta da O'Reilly em [2] (recomendo a leitura do capítulo 2 em específico para este assunto).

[1] https://stackoverflow.com/questions/10302179/hyphen-underscore-or-camelcase-as-word-delimiter-in-uris

[2] https://learning.oreilly.com/library/view/rest-api-design/9781449317904/

## Por que liberar url de Admin?

```python
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('call_records/', include('records.urls'))
]
```

Não vi nenhum uso para isso.

## Configurações estáticas de preço

```python
# -- utils.py

MINUTE_RATE = 0.09
CONNECTION_FEE = 0.36
```

No enunciado diz que o preço pode mudar, acho importante deixar isso customizável, até hoje vi duas formas de se fazer isso:

1. [mais complexa] Criar uma tabela de preços no banco de dados
2. [menos complexa] Tornar esses preços envvars que podem ser modificadas através do settings

# Notas específicas

## Admin

Rola remover o arquivo admin.py ;)

## Models

### Método save de CallEndRecord

> Este ponto não faz sentido pois causa recursão no signal, conversamos isso no bate-papo de feedback

```python
def save(self, *args, **kwargs):
    if self.price is None:
        try:
            call_start = CallStartRecord.objects.get(call_id=self.call_id)
        except CallStartRecord.DoesNotExist:
            pass
        else:
            self.price = calculate_call_rate(call_start.timestamp, self.timestamp)
    super().save(*args, **kwargs)
```

Essa lógica poderia facilmente ir para um signal, e acho que isso faria seu código ficar mais limpo. Exemplo de como poderia ser o signal:

```python
from .models import CallEndRecord, CallStartRecord
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=CallEndRecord)
def save_price(sender, instance, **kwargs):
    try:
        call_start = CallStartRecord.objects.get(call_id=instance.call_id)
    except CallStartRecord.DoesNotExist:
        pass
    else:
        instance.price = calculate_call_rate(call_start.timestamp, instance.timestamp)
        instance.save()
```

.... Edit ...

Baseado no papo que tivemos no feedback talvez dê pra usar o pre_save sem salvar a instância, exemplo:

```python
@receiver(pre_save, sender=CallEndRecord)
def save_price(sender, instance, **kwargs):
    try:
        call_start = CallStartRecord.objects.get(call_id=instance.call_id)
    except CallStartRecord.DoesNotExist:
        pass
    else:
        instance.price = calculate_call_rate(call_start.timestamp, instance.timestamp)
```

### CallStartRecord e CallEndRecord a respeito da alocação de espaço em disco

Parabéns por essa abordagem, o que eu tenho visto muito é a galera usando uma mesma tabela para armazenar o start e o end, a treta que isso gera é que, imagine assim:

```
Tabela Call

type           nullable=False   <start|end>
source         nullable=True
destination    nullable=True
timestamp      nullable=False
call_id        nullable=False
```

Este tipo de abordagem gera um desperdício de espaço, pois todos os registros de end ficarão com null em source e destination.

### Index de source e timestamp

Como o filtro da api vai ser realizado em cima de uma data de referência + source creio que os campos source e timestamp devem ser indexados para dar mais performance as buscas no endpoint de bills.

Você chegou a pensar nisso?

### Redefinição de objects em CallStartRecord

```python
objects = models.Manager()
```

Por que precisou fazer isso? Algum motivo especial?

### Redefinição de unique nas classes filhas

```python
class Meta:
    constraints = [
        models.UniqueConstraint(fields=['call_id'], name='callstartrecord_unique_callid')
    ]
```

Por que precisou fazer isso? No model base o campo de call_id já é `unique=True`

### Modelagem de CallEndRecord

Não vejo muito sentido o End armazenar o preço e também achei um pouco estranho esta entidade acessar coisas do start e ter um manager que também acessa coisas de start.

Sugestão para estudo: ter uma separação melhor das responsabilidades talvez ter um model específico para contabilizar as bills por período e source, como se fosse uma tabela de agregação. Ai você popula essa tabela ao final de cada end.

Porém essa sugestão é uma faca de dois gumes sempre, pois você dará mais velocidade para a leitura da tabela (uma vez que você não precisará rodar queries complexas para consultar um dado que já está agregado) mas perderá velocidade em escrita, pois para cada end que você adicionar vc deverá adicionar um bill, ai este tempo pode ficar alto.

### Testes de models

Pelo que entendi somente 2 testes de models foram criados:

1. `test_new_call_record_has_timestamp`: Testa o tipo do timestamp no model de start;
2. `test_new_call_record_has_price`: Testa preço no model de end;

Ao meu ver os dois testes não são necessários, pois:

- no teste 1 o framework já te garante esse comportamento uma vez que você disse que o campo é `DateTimeField` com certeza o tipo será um `datetime`
- no teste 2 você criou testes específicos para testar preço, então não faz sentido ter mais um teste pra testar isso, se o objetivo era testar o model isso não foi atingido pois o que vc acabou testando foi `calculate_call_rate` (no assert)

Quais casos eu sugiro cobrir nos testes de model:

- Passando todos os campos necessários devo criar um objeto
- Passando todos os campos exceto os opcionais devo criar um objeto
- Passando todos os campos exceto os obrigatórios NÃO devo criar um objeto
- Passando call id duplicado NÃO devo criar um objeto (este teste é mais pra garantir que nada do que vc fez mudará no futuro, pois essa é uma regra de negócio importante)

Exemplos de testes com models que podem ajudar:

- https://github.com/rafaelhenrique/wttd/blob/master/eventex/core/tests/test_model_talk.py
- https://github.com/rafaelhenrique/wttd/blob/master/eventex/core/tests/test_model_contact.py
- https://github.com/rafaelhenrique/wttd/blob/master/eventex/core/tests/test_model_speaker.py

## Querysets

Cara parabéns, pois mesmo com a complexidade da query você conseguiu fazer uma única query para resolver o problema que você tem.

A query final produzida pelo django é esta:

```sql
SELECT "records_callendrecord"."call_id", "records_callendrecord"."price", (SELECT U0."timestamp" FROM "records_callstartrecord" U0 WHERE U0."call_id" = ("records_callendrecord"."call_id")) AS "start", "records_callendrecord"."timestamp" AS "end", (SELECT U0."source" FROM "records_callstartrecord" U0 WHERE U0."call_id" = ("records_callendrecord"."call_id")) AS "source", (SELECT U0."destination" FROM "records_callstartrecord" U0 WHERE U0."call_id" = ("records_callendrecord"."call_id")) AS "destination", (("records_callendrecord"."timestamp")::timestamp with time zone - ((SELECT U0."timestamp" FROM "records_callstartrecord" U0 WHERE U0."call_id" = ("records_callendrecord"."call_id")))::timestamp with time zone) AS "duration" FROM "records_callendrecord" WHERE ("records_callendrecord"."timestamp" BETWEEN \'2017-12-01T00:00:00+00:00\'::timestamptz AND \'2018-01-01T00:00:00+00:00\'::timestamptz AND (SELECT U0."source" FROM "records_callstartrecord" U0 WHERE U0."call_id" = ("records_callendrecord"."call_id")) = \'99988526423\') ORDER BY "end" ASC  LIMIT 21
```

Tentei formatar mais desisti no meio hahaha....
Ai vem um desafio, mesmo ela estando rápida (local aqui deu 0.005) será que precisa usar tantas subqueries para chegar neste resultado?

Uma das abordagens interessantes que eu vi para resolver esse problema consiste em atribuir status para a call, por exemplo:

- "started": Só começou
- "finish": Começou e terminou
- "completed": Começou terminou e já tem preço calculado (pode ser um job assíncrono que calcula o preço)

Isso simplifica um pouco as coisas também.

### Testes de querysets

Aqui deixo um puxão de orelha... como que um queryset com uma função tão complexa e importante como essa fica sem testes? É importante ter testes para os ranges, por exemplo:

- Passei from_date > to_date o que acontece?
- Passei from_date < to_date o que acontece?
- Passei from_date < to_date e com um source que NÃO existe o que acontece?
- Passei from_date < to_date e com um source que existe o que acontece?

Tenta seguir aquela abordagem que te falei de "semi-TDD", caso não consiga ir pelo TDD raiz, nunca deixe para testar no final, sempre tente casar um pouco de teste + um pouco de código... isso vai ajudar muito no seu fluxo de pensamento também ;)

## Serializers

Comentários gerais: Muito bons os serializers, simples, sem muita lógica e fácil de ler ;)

### CallStartRecordSerializer

pass

### CallEndRecordCreateSerializer

pass

### CallRecordSerializer

pass

### Testes de serializers

Aqui temos umas questões complicadas, testes explícitos (unitátios) para os serializers não foram feitos, e ao invés disso você resolveu testar o fluxo completo.

Testar o fluxo completo é até ok, mas acaba deixando passar batidos erros específicos da unidade, então convêm (mesmo que repetidos as vezes) ter um teste mais voltado a integração das partes (teste de integração) e outros mais voltados a unidade (testes unitários)... mas sempre privilegiar os unitários.

Testes de integração que você fez que se relacionam com o serializer:

- test_new_call_start_record: No caso do primeiro 400 que você está testando
- test_new_call_start_record_requires_fields: Esse teste poderia ser feito especificamente nos serializers e talvez (caso deseje) repetir isso em um teste de integração
- test_new_call_start_record_with_duplicated_call_id: Call id duplicado é uma restrição do banco de dados, então deveria ter sido testado inicialmente no model
- test_new_call_start_record_with_destination: Já que você colocou a validação do destino no model, também faria mais sentido testar isso ou no model ou no serializer e repetir (talvez) no teste de integração

Sugestão para casos testes de serializers:

- Se eu passar todos os campos corretamente o objeto é validado corretamente (is_valid)?
- Se eu deixar de passar um campo que é requerido o objeto é validado (is_valid)?

Alguns exemplos de teste de serializers aqui:

- https://www.vinta.com.br/blog/2017/how-i-test-my-drf-serializers/

Dica: Por mais que os testes pareçam ser "bestas" isso garante que o comportamento da aplicação não quebre quando outro desenvolvedor vier codar no seu projeto... um teste bem feito serve de documentação para outro desenvolvedor.

## Views

### Por que TelephonyBillAPIView?

Traduzindo literalmente dá algo como "Conta de telefonia". Era essa a intenção mesmo?

### CallStartRecordAPIView

pass

### CallEndRecordAPIView

pass

### Método get de TelephonyBillAPIView

Cara, aqui notavelmente tem algo errado, estatísticas do método get:

- tem 28 linhas
- 8 condicionais
- 1 loop

Existe uma medida na computação chamada de complexidade ciclomática que diz que quanto mais ifs/desvios um código tem, mais complexo ele vai ser para uma pessoa entender, então isso pode ser preocupante neste método.

Com certeza da pra simplificar mais, vamos ver... Primeiramente podemos resolver tretas em relação ao período:

```python
period = request.query_params.get('period', None)
reference_month = datetime.strptime(period, "%Y-%m")
```

Com um código assim você já conseguiria resolver mais fácil algumas validações, pois da erro:

```
>>> reference_month = '2020-50'
>>> reference = datetime.strptime(reference_month, "%Y-%m")
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/home/rafael/.pyenv/versions/3.8.1/lib/python3.8/_strptime.py", line 568, in _strptime_datetime
    tt, fraction, gmtoff_fraction = _strptime(data_string, format)
  File "/home/rafael/.pyenv/versions/3.8.1/lib/python3.8/_strptime.py", line 352, in _strptime
    raise ValueError("unconverted data remains: %s" %
ValueError: unconverted data remains: 0
```

Então vamos arrumar só esse ponto por enquanto:

```python
### arquivo exceptions.py

from rest_framework.exceptions import APIException
from rest_framework.status import HTTP_422_UNPROCESSABLE_ENTITY

class UnprocessableEntityError(APIException):
    status_code = HTTP_422_UNPROCESSABLE_ENTITY

### Método da view em views.py

def clean_period(self, period=None):
    if not period:
        return

    try:
        period = datetime.strptime(period, "%Y-%m")
    except ValueError:
        raise ValidationError({"period": "Period is invalid."})

    today = timezone.now()

    same_year = today.year == period.year
    same_month = today.month == period.month

    if same_year and same_month:
        raise UnprocessableEntityError(
            {"period": "You can't get bills from current month."},
        )
    elif same_year and today.month < period.month:
        raise UnprocessableEntityError(
            {"period": "You can't get bills from next months."},
        )

    return period

```

Com este novo método acima você pode separar a lógica da "limpeza do período" (talvez o nome tenha ficado ruim, mas enfim hahaha). Continuando a refatoração, pode ser interessante também separar a lógica de achar o último mês..

```python
def get_last_month_first_and_last(self):
    today = timezone.now()
    first_day_of_month = today.replace(day=1)
    last_day_of_previous_month = first_day_of_month - timedelta(days=1)
    return (last_day_of_previous_month.replace(day=1), last_day_of_previous_month)
```

E por fim, refatorar o método `get`...

```python
import calendar  # lá em cima com os imports


def get(self, request, *args, **kwargs):
    source = request.query_params.get('source', None)
    period = request.query_params.get('period', None)
    period = self.clean_period(period)

    if not period:
        from_date, to_date = self.get_last_month_first_and_last()
    else:
        _, last_day = calendar.monthrange(period.year, period.month)
        from_date = period.replace(day=1)
        to_date = period.replace(day=last_day)

    if not source:
        raise ValidationError({'source': 'This field is required.'})

    records = CallEndRecord.objects.get_calls(from_date, to_date, source=source)
    serializer = CallRecordSerializer(records, many=True)
    return Response({
        'source': source,
        'start_period': from_date,
        'end_period': to_date,
        'records': serializer.data
    })
```

Na minha opinião isso vai facilitar a leitura e tornar mais visíveis determinados problemas que podem vir a acontecer.

PS: Testei porcamente essa refatoração, caso você deseje seguir esse caminho é importante analisar todo o código que eu coloquei acima com a calma de um monge, pois fiz na correria e posso ter errado em algum ponto ;)

### Pegadinha pilantra do enunciado vs TelephonyBillAPIView

Este trecho do enunciado é uma pegadinha muito das pilantras...

```
To get a telephone bill we need two information: the subscriber telephone
number (required); the reference period (month/year) (optional). If the 
reference period is not informed the system will consider the last closed 
period. In other words it will get the previous month. It's only possible to 
get a telephone bill after the reference period has ended.
```

Por que é das muitos pilantras? Pois na olist a gente usa o seguinte padrão para listagem de coisas [3]:

```
METHOD  URL                      STATUS  RESPONSE
GET     /users                   200     [John, Peter]
GET     /users/john              200     John
GET     /users/kyle              404     Not found
GET     /users?name=kyle         200     []
DELETE  /users/john              204     No Content
```

Então vamos pensar sobre esse endpoint, seguindo a abordagem de lista:

```
METHOD    URL                                                    STATUS    RESPONSE
GET       /call_records/bills?source=99988526423&period=2017-12  200       [conta1, conta2]
```

Este tipo de busca com parâmetros obrigatórios limita um pouco as nossas possibilidades como consumidor da api, penso que algo mais "agradável" seria:

```
METHOD    URL                                                  STATUS    RESPONSE
GET       /call_records/bills                                  200       [conta1, conta2, conta4, conta5]
GET       /call_records/bills?source=<source>&period=<period>  200       [conta1, conta2]
```

Por que eu digo isso? Pois eu tenho mais maleabilidade para fazer os filtros que eu bem entender.

Porém no enunciado diz "the subscriber telephone number (required)", e isso confunde 99.9% das pessoas.... e isso é bom, pois assim eu posso explicar como a Olist faz as coisas :).

Mas tirando o lero-lero pra lá, eu não concordo com o source obrigatório, acho que uma vez que o usuário da api não passa o source uma listagem completa de todas as bills paginadas deveria ser exibida.

Mas eu acredito SIM que o que você fez atende o que o enunciado pede, só não gosto de deixar essa discussão passar em branco :).

Outra coisa que eu acho meio estranha/errada é trazer o último mês quando você não passa parâmetros de month e year (como pede o enunciado), na minha cabeça o comportamento deveria ser o mesmo quando vc não passar source... uma listagem completa de todas as bills paginadas deveria ser exibida. Isso de ter valores "default" inclusive vai contra os princípios do django-filter [1] [4].

Esse tipo de "liberdade" que a gente dá na API é interessante, pois nunca sabemos o que os nossos usuários pedirão em seguida, e quando trabalhamos com querystrings para estes tipos de questão tudo fica mais simples.

Deixo também uma referência bem interessante sobre alguns patterns de design de uris de uma API Rest [2].

[1] https://django-filter.readthedocs.io/en/master/guide/usage.html

[2] https://learning.oreilly.com/library/view/rest-api-design/9781449317904/ch02.html

[3] https://stackoverflow.com/questions/11746894/what-is-the-proper-rest-response-code-for-a-valid-request-but-an-empty-data

[4] https://django-filter.readthedocs.io/en/master/guide/tips.html#using-initial-values-as-defaults


### Testes de views

#### Faltando testes em CallEndRecordAPITestCase

Por que tantos testes para o start e somente um para o end?

#### Tem testes falhando!!

```
$ python manage.py test
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
F.F.FF.....
======================================================================
FAIL: test_calculate_call_rate (records.tests.CalculateCallRateTestCase) (index=5)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/rafael/repositorios_git/olist/mentoria/caio-assis/records/tests.py", line 56, in test_calculate_call_rate
    self.assertEqual(
AssertionError: 86.76 != 86.85

======================================================================
FAIL: test_calculate_call_rate (records.tests.CalculateCallRateTestCase) (index=6)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/rafael/repositorios_git/olist/mentoria/caio-assis/records/tests.py", line 56, in test_calculate_call_rate
    self.assertEqual(
AssertionError: 173.16 != 173.25

======================================================================
FAIL: test_new_call_end_record (records.tests.CallEndRecordAPITestCase)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/rafael/repositorios_git/olist/mentoria/caio-assis/records/tests.py", line 156, in test_new_call_end_record
    self.assertEqual(response.status_code, HTTP_201_CREATED)
AssertionError: 415 != 201

======================================================================
FAIL: test_new_call_start_record (records.tests.CallStartRecordAPITestCase)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/rafael/repositorios_git/olist/mentoria/caio-assis/records/tests.py", line 99, in test_new_call_start_record
    self.assertEqual(response.status_code, HTTP_201_CREATED)
AssertionError: 415 != 201

======================================================================
FAIL: test_new_call_start_record_with_destination (records.tests.CallStartRecordAPITestCase)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/rafael/repositorios_git/olist/mentoria/caio-assis/records/tests.py", line 130, in test_new_call_start_record_with_destination
    self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
AssertionError: 415 != 400

======================================================================
FAIL: test_new_call_start_record_with_duplicated_call_id (records.tests.CallStartRecordAPITestCase)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/rafael/repositorios_git/olist/mentoria/caio-assis/records/tests.py", line 118, in test_new_call_start_record_with_duplicated_call_id
    self.assertEqual(response.status_code, HTTP_201_CREATED)
AssertionError: 415 != 201

----------------------------------------------------------------------
Ran 12 tests in 0.063s

FAILED (failures=6)
Destroying test database for alias 'default'...
```

Todos os 415 acima faltam formato, para corrigir:

```python
response = self.client.post(self.post_url, data, format='json')
```

#### test_new_call_start_record

O que testa esse teste? Qual o objetivo dele? Pelo nome eu entendo que é a criação de uma nova call de start, porém no começo eu vejo um post e em seguida um 400, e depois de fato vejo a criação de uma call.

Primeiro ponto, acho que o nome tem que fazer sentido, por exemplo:

`test_create_start_record_success`

E separar o caso de teste de erro de dentro deste teste.

#### test_new_call_start_record_requires_fields

Esse teste é interessante, mas eu acharia mais seguro remover um campo requerido por vez e retestar senão pode ter alguma anomalia que a criação não funciona somente se faltarem aqueles 4 campos e o teste passa se um deles faltar por exemplo, minha recomendação seria algo assim:

```python
def test_new_call_start_record_requires_fields(self):
    required_fields = ['call_id', 'destination', 'source', 'timestamp']
    payload = {
        'source': '505',
        'destination': '1234567890',
        'call_id': '12345',
        'timestamp': self.today
    }

    for field in required_fields:
        with self.subTest(field=field):
            test_payload = payload.copy()
            del test_payload[field]
            response = self.client.post(self.post_url, test_payload)
            self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
            self.assertContains(response.data, field)
```

O subTest é bem interessante para realizarmos estes tipos de teste pois ele isola o contexto entre um e outro e se um falhar fica fácil de visualizarmos.

Referência: https://docs.python.org/3/library/unittest.html#distinguishing-test-iterations-using-subtests

#### test_new_call_start_record_with_duplicated_call_id

Esse teste tem 2 posts, não acho legal criar coisas do setup do teste com post, pois isso de alguma maneira pode invalidar o teste se uma coisa estiver privilegiando outra, então como o seu foco é o segundo post, foque nele, e para fazer as criações de "setup" você pode criar utilizando factory-boy [1] ou o próprio orm do Django mesmo para pré-popular os dados.

[1] https://factoryboy.readthedocs.io/en/latest/introduction.html

#### test_new_call_start_record_with_destination

Neste caso a mesma coisa, sinto que esse teste é para testar call de start COM DESTINO, mas logo no começo testa sem destino para validar se irá acontecer o 400, neste caso, convêm separar o teste, pois o objetivo se perdeu no meio ;)

#### test_new_call_end_record

Quando temos muitas asserções em cima de dados convêm testar o dict todo, sugestão:

```python
def test_new_call_end_record(self):
    call_id = self.call_start_record.call_id
    timestamp = self.call_start_record.timestamp + timedelta(minutes=5)
    response = self.client.post(self.post_url, {'call_id': call_id, 'timestamp': timestamp}, format='json')
    self.assertEqual(response.status_code, HTTP_201_CREATED)

    content = response.json()
    del content['call_id']
    del content['id']
    self.assertDictEqual(content, {
        'timestamp': '2020-03-18T19:40:51.666924Z',
        'price': '0.81'
    })
```

Para as datas não mudarem podemos usar a biblioteca freezegun [1].

[1] https://github.com/spulec/freezegun

#### setUpTestData de TelephonyBillAPITestCase

Não tem como simplificar esse setUpTestData? Vi que tem MUITOS casos ali, será que precisa de tudo isso mesmo para todos os testes da classe? E se precisa, não compensa criar um loop para fazer essas criações?

#### test_retrieve_telephony_bill

Para este teste eu adotaria a saída do dict que mostrei acima, pois aparentemente a lógica para comparar se está certo/errado ficou bem complexa.

#### test_retrieve_telephony_bill_of_this_month

Esse testa testa o BAD REQUEST, mas e a mensagem? Será mesmo que este BAD REQUEST aconteceu pelo motivo que você queria que acontecesse? Isso é bem importante de se avaliar em um teste.

#### test_retrieve_telephony_bill_of_next_month

Neste teste acho que o freezegun pode te ajudar novamente, não fica legal usarmos ifs/loops dentro dos nossos testes, somente em último caso.

Pelo que vi aqui você usou o loop pois buscou a data a partir do now, e isso não é recomendado em testes, é legal ter um tempo fixo para garantir que você está fazendo a asserção naquilo que foi o previsto (infelizmente o imprevisto entregamos a deus... amém hahaha).

#### test_retrieve_telephony_bill_without_source

Aqui novamente o bad request, por que? Será que esse é mesmo bad request que vc queria receber? Será que não é outro?

É bacana fazer um assert da mensagem ;)

## Utils

Cara nesse utils inteiro só tenho uma ressalva, os preços TEM que ser dinâmicos:

```
It's important to notice that the price rules can
change from time to time, but an already calculated
call price can not change.
```

Ai pelo que eu sei atualmente tem duas formas de resolver isso:

1. [mais complexo] Criando uma tabela de preço e controlando os preços por api
2. [mais simples] Transformando os valores fixos em envvar e permitindo a mudança rápida caso seja necessário

### Testes de utils

Parabéns pelos testes! O CalculateCallRateTestCase ficou bem bom :)

Porém desta vez que eu estava revisando 2 testes quebraram:

```
======================================================================
FAIL: test_calculate_call_rate (records.tests.CalculateCallRateTestCase) (index=5)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/rafael/repositorios_git/olist/mentoria/caio-assis/records/tests.py", line 56, in test_calculate_call_rate
    self.assertEqual(
AssertionError: 86.76 != 86.85

======================================================================
FAIL: test_calculate_call_rate (records.tests.CalculateCallRateTestCase) (index=6)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/rafael/repositorios_git/olist/mentoria/caio-assis/records/tests.py", line 56, in test_calculate_call_rate
    self.assertEqual(
AssertionError: 173.16 != 173.25
```

Convêm dar uma olhada depois ;)
