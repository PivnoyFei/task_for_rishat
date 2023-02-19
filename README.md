

[![Build Status](https://github.com/PivnoyFei/task_for_rishat/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/PivnoyFei/task_for_rishat/actions/workflows/main.yml)

<h1 align="center"><a target="_blank" href="">Тестовое задание для VoxWeb Interactive</a></h1>

### Стек
![Python](https://img.shields.io/badge/Python-171515?style=flat-square&logo=Python)![3.10](https://img.shields.io/badge/3.10-blue?style=flat-square&logo=3.10)
![Django](https://img.shields.io/badge/Django-171515?style=flat-square&logo=Django)![4.1.7](https://img.shields.io/badge/4.1.7-blue?style=flat-square&logo=4.1.7)
![Django Rest Framework](https://img.shields.io/badge/Django--Rest--Framework-171515?style=flat-square&logo=Django)![3.14.0](https://img.shields.io/badge/3.14.0-blue?style=flat-square&logo=3.14.0)
![SQLite](https://img.shields.io/badge/SQLite-171515?style=flat-square&logo=SQLite)
![Admin-LTE-3](https://img.shields.io/badge/Admin--LTE--3-171515?style=flat-square&logo=Admin-LTE-3)

### Задание
Реализовать Django + Stripe API бэкенд со следующим функционалом и условиями:
- Django Модель Item с полями (name, description, price) 
- API с двумя методами:
- - GET /buy/{id}, c помощью которого можно получить Stripe Session Id для оплаты выбранного Item. При выполнении этого метода c бэкенда с помощью python библиотеки stripe должен выполняться запрос stripe.checkout.Session.create(...) и полученный session.id выдаваться в результате запроса
- - GET /item/{id}, c помощью которого можно получить простейшую HTML страницу, на которой будет информация о выбранном Item и кнопка Buy. По нажатию на кнопку Buy должен происходить запрос на /buy/{id}, получение session_id и далее  с помощью JS библиотеки Stripe происходить редирект на Checkout форму stripe.redirectToCheckout(sessionId=session_id)
- - Пример реализации можно посмотреть в пунктах 1-3 тут
- Залить решение на Github, описать запуск в Readme.md
- Опубликовать свое решение чтобы его можно было быстро и легко протестировать. 
- Решения доступные только в виде кода на Github получат низкий приоритет при проверке.

Бонусные задачи: 
- Запуск используя Docker
- Использование environment variables
- Просмотр Django Моделей в Django Admin панели
- Запуск приложения на удаленном сервере, доступном для тестирования
- Модель Order, в которой можно объединить несколько Item и сделать платёж в Stripe на содержимое Order c общей стоимостью всех Items
- Модели Discount, Tax, которые можно прикрепить к модели Order и связать с соответствующими атрибутами при создании платежа в Stripe - в таком случае они корректно отображаются в Stripe Checkout форме. 
- Добавить поле Item.currency, создать 2 Stripe Keypair на две разные валюты и в зависимости от валюты выбранного товара предлагать оплату в соответствующей валюте
- Реализовать не Stripe Session, а Stripe Payment Intent.



### Маршруты
| Название | Метод | Описание | Авторизация |
|----------|-------|----------|-------------|
|                            | GET  | Список товаров и поиск по названию | нет
| order/<str:username>/      | GET  | Страница заказа            | Да
| order_list/<str:username>/ | GET  | Список выполненых заказов  | Да
| item/<int:pk>/             | GET  | Посмотреть товар           | Да
| buy/<int:pk>/              | GET  | Купить товар               | Да
| item/<int:pk>/add/         | POST | Добавляет товар в заказ    | Да
| item/<int:pk>/remove/      | POST | Удаляет товар из заказа    | Да


### Запуск проекта
Клонируем репозиторий и переходим в него:
```bash
gh clone https://github.com/PivnoyFei/task_for_rishat.git
cd task_for_rishat
```

#### Создаем и активируем виртуальное окружение:
```bash
python3 -m venv venv
source venv/bin/activate
```
#### для Windows
```bash
python -m venv venv
source venv/Scripts/activate
```
#### Обновиляем pip и ставим зависимости из requirements.txt:
```bash
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

### Перед запуском сервера, необходимо создать .env файл расположенный по пути infra/.env со своими данными.
### Ниже представлены параметры по умолчанию.
```bash
SECRET_KEY='key' # Секретный ключ джанго
DEBUG='True' # Режим разработчика
ALLOWED_HOSTS='localhost' # Адрес

DB_ENGINE='django.db.backends.postgresql'
DB_NAME='postgres' # имя БД
POSTGRES_USER='postgres' # логин для подключения к БД
POSTGRES_PASSWORD='postgres' # пароль для подключения к БД
DB_HOST='db' # название контейнера
DB_PORT='5432' # порт для подключения к БД

# Обязательно иметь ключи для запуска!
STRIPE_PUBLIC_KEY='pk_test_key'
STRIPE_SECRET_KEY='sk_test_key'
```

#### Чтобы сгенерировать безопасный случайный секретный ключ, используйте команду:
```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### Для запуска в Docker:
#### Переходим в папку с файлом docker-compose.yaml:
```bash
cd infra
```

#### Запуск docker-compose:
```bash
docker-compose up -d --build
```

#### Примените миграции:
```bash
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate --noinput
```

#### Создайте суперпользователя Django:
```bash
docker-compose exec backend python manage.py createsuperuser
```

#### После успешной сборки, если админа не работает, на сервере выполните команды (только после первого деплоя):
```bash
docker-compose exec backend python manage.py collectstatic --noinput
```

#### Останавливаем контейнеры:
```bash
docker-compose down -v
```

### Запуск на локальной машине:
#### Открываем в консоли папку backend:
```bash
cd backend
```

#### Обновиляем pip и ставим зависимости из requirements.txt:
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

#### Примените миграции:
```bash
python manage.py makemigrations
python manage.py migrate --noinput
```

#### Создайте суперпользователя Django:
```bash
python manage.py createsuperuser
```

#### Запускаем сервер:
```bash
python manage.py runserver
```

#### При первом запуске парсера потребует ввести номер телефона и код из телеграм:

Теперь по адресу http://localhost:8000/admin/ доступна админка.

#### Автор
[Смелов Илья](https://github.com/PivnoyFei)