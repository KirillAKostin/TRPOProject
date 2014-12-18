from datetime import datetime
import json
from django.http import HttpResponse
from django.shortcuts import render
from dishes.models import EstablishmentDish, Dish
from employees.models import Employee
from establishments.models import EstablishmentBranch, DinnerWagon, Establishment
from orders.models import Order
from orders.forms import TableForm
from orders.forms import DeliveryForm
from orders.forms import PickUpForm


def view_cart(request, cart_state):
    """Отображает страницу корзины заказа"""
    """cart_state == '1' - загружаем из сессии параметры корзины"""
    """cart_state == '0' - очищаем ключи сессии, загружаем пустую корзину"""
    if cart_state == '0':
        request.session.flush()
        cart_price = 0
        return render(
            request,
            'orders/cart.html',
            {
                'cart_price': cart_price
            }
        )
    else:
        if request.session.get('cart_price') is not None:
            cart_price = request.session.get('cart_price')
        else:
            cart_price = 0

        if cart_price == 0:
            return render(
                request,
                'orders/cart.html',
                {
                    'cart_price': cart_price
                }
            )
        else:
            dishes = {}
            for key in request.session.keys():
                if key != 'cart_price':
                    dishes[EstablishmentDish.objects.get(dish__id=key)] = request.session.get(key)
            cart_dishes = dishes.items()
            return render(
                request,
                'orders/cart.html',
                {
                    'cart_price': cart_price,
                    'cart_dishes': cart_dishes,
                }
            )


def view_orders(request):
    """Отображает страницу подготовленных заказов"""
    order_establishments = []
    for key in request.session.keys():
        if key != 'cart_price':
            first_establishment_for_key = EstablishmentDish.objects.filter(dish__id=int(key))[0].establishment
            if order_establishments.count(first_establishment_for_key) == 0:
                order_establishments.append(first_establishment_for_key)

    orders_in_cart = {}
    for establishment in order_establishments:
        establishment_order_price = 0
        for key in request.session.keys():
            if key != 'cart_price':
                if EstablishmentDish.objects.filter(dish__id=int(key))[0].establishment.name == establishment.name:
                    establishment_order_price += \
                        request.session[key] *\
                        EstablishmentDish.objects.get(dish__id=int(key)).dish.price
        orders_in_cart[establishment] = establishment_order_price

    orders = orders_in_cart.items()

    return render(
        request,
        'orders/cart_orders.html',
        {
            'orders': orders
        }
    )


def view_establishment_dish_list(request):
    if request.is_ajax():
        establishment_id = request.GET.get('id')
        establishment = EstablishmentDish.objects.filter(establishment__id=int(establishment_id))[0].establishment
        establishment_dishes_in_order = {}
        for key in request.session.keys():
            if key != 'cart_price':
                if EstablishmentDish.objects.filter(dish__id=int(key))[0].establishment.name == establishment.name:
                    establishment_dishes_in_order[Dish.objects.get(id=int(key))] = request.session[key]

        dish_list = []
        for key, val in establishment_dishes_in_order.items():
            dish_specification = {'dish_name': key.name, 'dish_price': key.price, 'dish_count': val}
            dish_list.append(dish_specification)

        json_string = json.dumps(dish_list, ensure_ascii=False).encode('utf8')
        return HttpResponse(json_string)
    else:
        return HttpResponse('error')


def increment_dish(request):
    """Увеличивает количество единиц заданного блюда на 1"""
    if request.is_ajax():
        dish_id = request.GET.get('id')
        dish_price = request.GET.get('price')
        request.session[dish_id] += 1
        request.session['cart_price'] += float(dish_price)
        return HttpResponse(request.session[dish_id])
    else:
        return HttpResponse('error')


def decrement_dish(request):
    """Уменьшает количество единиц заданного блюда на 1"""
    if request.is_ajax():
        dish_id = request.GET.get('id')
        dish_count = request.GET.get('count')
        old_count = request.session.get(dish_id)
        dec_price = Dish.objects.get(id=dish_id).price * int(dish_count)
        if old_count - int(dish_count) <= 0:
            del request.session[dish_id]
            old_cart_price = request.session.get('cart_price')
            if old_cart_price - dec_price <= 0:
                del request.session['cart_price']
            else:
                request.session['cart_price'] -= dec_price
        else:
            request.session[dish_id] -= int(dish_count)
            request.session['cart_price'] -= dec_price
        if request.session.get(dish_id) is not None:
            return HttpResponse(request.session[dish_id])
        else:
            return HttpResponse(0)
    else:
        return HttpResponse('error')


def get_form(request, establishment_id, order_type):
    """Возвращает на страницу соответствующую форму, тип зависит от order_type:
    0 - заказ столика
    1 - заказ самовывоза
    2 - заказ доставки"""
    # проверям, нужно ли вообще пользователю показывать форму (вдруг он ничего не заказал?)
    # проверяем, есть ли в сессии ключи, соответствующие блюдам выбранного заведения
    establishment_dishes = Dish.objects.filter(establishmentdish__establishment__id=establishment_id)
    is_valid_request = False
    for key in request.session.keys():
        if key != 'cart_price':
            if establishment_dishes.get(id=key) is not None:
                is_valid_request = True

    if is_valid_request:
        order_types = Order.ORDER_TYPE
        if order_type == '1':
            if request.method == 'POST':
                form = PickUpForm(establishment_id, request.POST)
            else:
                form = PickUpForm(establishment_id)
            show_errors = 1
            return render(
                request,
                'orders/make_order_form.html',
                {
                    # show_form определяет, нужно ли показывать форму пользователю
                    'show_form': 1,
                    'show_errors': show_errors,
                    'establishment_id': establishment_id,
                    'form': form,
                    'order_types_list': order_types,
                    'current_order_type': order_type
                }
            )
        elif order_type == '2':
            if request.method == 'POST':
                form = DeliveryForm(request.POST)
            else:
                form = DeliveryForm()
            show_errors = 1
            return render(
                request,
                'orders/make_order_form.html',
                {
                    # show_form определяет, нужно ли показывать форму пользователю
                    'show_form': 1,
                    'show_errors': show_errors,
                    'establishment_id': establishment_id,
                    'form': form,
                    'order_types_list': order_types,
                    'current_order_type': order_type
                }
            )
        else:
            if request.method == 'POST':
                if request.POST.get('address_changed') == '1':
                    branch_id = request.POST.get('address')
                    form = TableForm(establishment_id, branch_id, -1, request.POST)
                    show_errors = 0
                elif request.POST.get('hall_changed') == '1':
                    branch_id = request.POST.get('address')
                    hall_type = request.POST.get('hall')
                    form = TableForm(establishment_id, branch_id, hall_type, request.POST)
                    show_errors = 0
                else:
                    branch_id = request.POST.get('address')
                    hall_type = request.POST.get('hall')
                    form = TableForm(establishment_id, branch_id, hall_type, request.POST)
                    show_errors = 1
                    if form.is_valid():

                        # создание и запись в БД заказа
                        order_client_phone = form.cleaned_data['phone']
                        order_order_type = order_type
                        date_time_data = form.cleaned_data['datetime']
                        order_execute_datetime = datetime(
                            date_time_data.year,
                            date_time_data.month,
                            date_time_data.day,
                            date_time_data.hour,
                            date_time_data.minute
                        )
                        order_contact_account = Employee.objects.filter(
                            establishment__id=establishment_id
                        ).first()
                        order_branch_id = int(request.POST.get('address'))
                        order_establishment_branch = EstablishmentBranch.objects.filter(
                            id=order_branch_id
                        ).first()
                        order_table_seats = int(request.POST.get('table'))
                        order_hall_type = request.POST.get('hall')
                        order_dinner_wagon = DinnerWagon.objects.filter(
                            is_reserved=False,
                            seats=order_table_seats,
                            hall__type=order_hall_type,
                            hall__branch=order_establishment_branch
                        ).first()
                        new_order = Order(
                            client_phone=order_client_phone,
                            type=order_order_type,
                            execute_datetime=order_execute_datetime,
                            contact_account=order_contact_account,
                            establishment_branch=order_establishment_branch,
                            dinner_wagon=order_dinner_wagon
                        )
                        new_order.make(type='table')
                        new_order.save()

                        # удаление из сессии оформленных в заказе блюд и корзины, при необходимости
                        keys_for_delete = []
                        for key in request.session.keys():
                            if key != 'cart_price':
                                if establishment_dishes.get(id=key) is not None:
                                    keys_for_delete.append(key)
                        for key in keys_for_delete:
                            del request.session[key]
                        is_cart_empty = True
                        for key in request.session.keys():
                            if key != 'cart_price':
                                is_cart_empty = False
                        if is_cart_empty:
                            del request.session['cart_price']

                        # TODO редирект на страницу успешного оформления заказа
                        establishment = Establishment.objects.get(id=establishment_id)
                        return render(
                            request,
                            'orders/order_created.html',
                            {
                                'order_type': order_type,
                                'establishment_id': establishment_id,
                                'establishment_name': establishment.name,
                                'establishment_email': establishment.email,
                                'establishment_branch_order_phone': order_establishment_branch.order_phone_number,
                                'establishment_branch_help_phone': order_establishment_branch.help_phone_number
                            }
                        )
            else:
                form = TableForm(establishment_id, -1, -1)
                show_errors = 0
            return render(
                request,
                'orders/make_order_form.html',
                {
                    # show_form определяет, нужно ли показывать форму пользователю
                    'show_form': 1,
                    'show_errors': show_errors,
                    'establishment_id': establishment_id,
                    'form': form,
                    'order_types_list': order_types,
                    'current_order_type': order_type
                }
            )
    else:
        show_errors = 0
        return render(
            request,
            'orders/make_order_form.html',
            {
                # show_form определяет, нужно ли показывать форму пользователю
                'show_form': 0,
                'show_errors': show_errors,
                'establishment_id': establishment_id
            }
        )
