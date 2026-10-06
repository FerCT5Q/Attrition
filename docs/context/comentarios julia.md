

## Applied to a job

No tenemos datos mas recientes?el ultimo año disponible en el slide es FY2024. Lo que me extraña un poco es que subieron las aplicaciones.
Creo que podemos usar la variable si hay datos actuales, y los dividria como:

employee aplico a:
type1 - 0 veces
type2 - 1 vez
type3 - +1 vez


Potencial: Alto





## Transfer within past year

Duda: Me parece alto el numero de transfers en los ultimos 6  meses, si estamos usando tranfers? es que hay una columna que nos dice que tipo de transfers, porque unas son promos otras si son transfers c2c
pero quizas no valga la pena meterlo, y mejor ponerla como cuanto tiempo lleva en su rol sin importar si llego ahi por transfer, por su rol o etc.


Potencial: Bajo




## Location
## Region
## Market

Se me hace raro que a India no lo pongan con markets, pero entonces asumiendo que por algo existe los markets, que hay mas competencia,
MI propuesta sería que usaramos REGION y MARKET

con esto ya separamos india solito y separamo zonas de lso paises que sean competitivos.


Potencial: Alto





## office site and city

Me parece buena variable, quizas podria ser market u office site, en el caso de india nos da una mejor division de zonas


Potencial: Alto




## Team turnover
## High risk manager
## High turnover under this person

esta me parece buena, aunque no estoy muy segura de que interprete correctamete los porcentajes
Creo que para esta lo que podriamos hacer es si 3.11% es el promedio de attrition por manager
entonces como que marcar 1 si el employe se encuentra con un manager que maneja un attrition por arriba del promedio.

Ejemplo: Leah tiene en promedio un attrition de su equipo del 5% semestral, limitarlo a que al menos tenga 1.5 años por ejemplo
(hay que ver como rastrear el historico del manager y como manjeamos new hires; se me ocurre que al menos tengan los empleados 6 meses con ese manager para evaluar el attrition)
. Y si decimos que en promedio de attrition es de 7%
en este caso nosotros tendriamos 0 como indicador para este team turnover, pero si estamos con ROb que tiene 9%, esos tendrían 1

no sé si este confundiendo esta de team turnover por la de manager

Potencial: Alto



## More than 1 employee leaves

No entendi la grafica :(





## Job family

Nos da buena visibilidad de como cambio, pero como deciamos solo es para definir el scope, sera que al msno tengan un año de historico las nuevas familias, no?

Potencial: Baja






## Gender

vaya vaya.... tacubaya  bueno saber pero no la usariamos porque no podemos accionar sobre genero por politicas qualcomm


Potencial: Baja





## Remote/hybrid

Podmeos poner 1 y 0, es onsite = 1, cualquier otro valor sería 0.


Potencial: Alta





## Engineering

Usemosla, y no se si deberiamos usar mejor CTO y Corp

Potencial: Alta





## Rehire
podemos usarla como 1 y 0s, y si acaso un analisis extra sería ver el turnover de los hires vs rehires

Potencial: Media





## Years of experience prior to QUalcomm

creo que esta valdria la pena ver el attrition anual para saber como agrupamos esta variable porque podriamos asumir que gente mas senior es mas dificl que rote
pero quizas tenga mas ofertas de trabajo fuera.

De inicio pensaria que la agrupemos como menor a 1 año de espereicnea, de 1 a 3, 3 a 5, de 5 a 10, 10 a 15 y mas de 15 quizas...


Potencial: alta





## Commute distance

creo que solo falta validar que esos 50218 employees sean onsite porque lso offsite da lo mismo que tna lejos esten y seguramente estaran lejos

No se como debamos usar esta vairable, por lo mismo que no significa 30km en California vs Ciudad de Mexico. Quiza podamos combianarla con pais, estado o usar una variable externa
como si es mas de 20km y estas en el top 10 de ciudad con mayor trafico, alerta pero la podemos poner en fase 2 o 3


Potencial: Media





## RTO/hybrid comment in QVoice

Esta me gusta, creo que no es necesario separar por remote, hybrud, rto. EL hecho de que mencionen el tema creo que ya es valido,
Podriamos usar 1s y 0s


Potencial: Alto





#Retention concerns in QVoice comments

Podemos usarlo, por ejemplo de que si se qquejan del manager, workload o home office. 
Podriamos tener 3 variables, un topico por vairbale y asignar 1s y 0s. 


Potencial: Media





#Non respondents

Usemosla
Potencial: Alta





## Intent to stay
## career goals item
## engagement?

lo mismo 1s y 0s, seguro nos ayuda. La otra opcion que se me ocurre es si deberiamos hacer un hearhbeat
y decir si la persona califico intent to stay, career goals, engagement, por abajo de su promedio, menos 1-2 varianzas


Potencial: Alto





## Average of all qvoice items
no se si debamos usarla, podriamos ver el attrition como los favorables vs los unfavorables porque puede ser que la gentea
califique negativo pero asi es siempre, como usted. y siguien ahi

Potencial: Bajo




## Time in current job profile
## How employees reached their current compensation grade

esta definitivamente,  pero valdra la pena separar si llegaron por promotion o por hire porque el attrition es distinto
si llegaron por promotion el pico es a los 2 años. enotnce spodemos poner por:
menos de 1 año
de 1 a 2 años
2 a 4 
4 a 5
y mas de 5


luego si son new hire, estan esperando su primera promo, deberia ser algo asi de menos de 2 años, luego 2 a 3 , de 3 a 4, mas de 4

Potencial: Alto





## Company tenure
## time since last promotion

NO se si usemos esta se empalmen con la anterior de cuanto llevne en la psociion, porque ya que llevne mucho años son mas resilientes creo yo
igual con el hehco de que esten esperando una promocion, creo que la anterior resume mejor cual es el attrition

Potencial: Baja





## COmpensation Grade
## Level

si debemos usarlo, pero aqui creo que va a ser como separar si son entry level que seiran 10-20, core  que va aprox de 30 a 50 y senior mayor a 60.
peero aca tambien importa el track.  O meter asi el compensation grade y haber como nos agrupa el modelo el compensation grade, pero definitivmanete si lo usariamos

O usar level, creo que una de las dos

Potencial: Alto





## Layers

Se ve bien, lo pongo en medio porque no se que tnato influya pero lo podemos meter


Potencial: Medio



ffffff
==============================================================================================


#Compensation Ratio, 

Creo que los que tenga entre .8 y .9, luego menos de .8 podria tener mayor riesgo.
Se podria evaluar el attrition en esos dos grupos porque ya sea que agrupemos en 2 o un solo grupo 
O ya lo metemos asi al modelo pero creo que puede funcionar

Potencial: Alto





#within team compensation range

no me queda claro que esos de flagged group.





# co-location with manager

ok

Potencial: medio





#Residential distance from manager

creo que esto mas bien tiene que ver si estan en la misma oficna y sino seria ver si estan menos de 4 horas de difernecia oa sm de 4 horas de diferneica





## Manager leaving

Creo que esta seria ver como ser mas exactos, no estoy segura. si marcarlo como 1 exposed o no exposed, podríamos porbar

Potencial: Medio





## Number of manager changes

Aca creo que seria, que tan frecuente es que un empleado cambie de manager y que la persona no haya tenido un transfer ni una promo. para evitar que no se considere esos casos


Potencial: Medio






## Talent index

ahm aca no se que se grafico porque de 90-100 en teoria deberia estar el 10% de lo employees
quizas es ver como se ve el attrtion  en cada grupo y ver si vale la pena meterlo


Potencial: Medio







los ultimos 2 slides no le cache jeje. Creo que falto tmabien de que tamaño es el euipo, que seria "Span" y no se si falten mas variables, ademas del qvoice pero
del qvoice seria engagement, intent to stay y career goals.

 