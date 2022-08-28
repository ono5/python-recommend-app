from typing import Union
from flask import Flask, render_template, request, url_for, redirect

from app.controllers.forms import RateForm, YesOrNoForm
from app.models.user import User
from app.models.restaurant import Restaurant
from app.models.rate import Rate
import settings

app = Flask(__name__, template_folder=settings.TEMPLATE_FOLDER,
            static_folder=settings.STATIC_FOLDER)


class WebServer(object):
    def start(self, debug=False):
        app.run(host="0.0.0.0", port=settings.PORT, debug=debug)


server = WebServer()

ROBOT_NAME = 'Roboko'


@app.route("/", methods=["GET", "POST"])
def hello() -> str:
    if request.method == "POST":
        user_name = request.form.get("user_name").strip()
        user = User.get_or_create(user_name)
        restaurants = Rate.recommend_restaurant(user)
        if restaurants:
            form = YesOrNoForm(request.form)
            form.user_name.data = user_name
            return render_template("recommend_restaurant.html", user_name=user_name, restaurants=restaurants, form=form)

        form = RateForm(request.form)
        form.user_name.data = user_name
        return render_template("evaluate_restaurant.html", user_name=user_name, form=form)

    return render_template("hello.html", name=ROBOT_NAME)


@app.route("/restaurant/evaluate/status", methods=["GET", "POST"])
def evaluate_yes_or_no() -> str:
    if request.method == "POST":
        form = YesOrNoForm(request.form)
        user_name = form.user_name.data.strip()
        if form.value.data == "No":
            return render_template("good_bye.html", user_name=user_name)

        form = RateForm(request.form)
        form.user_name.data = user_name
        return render_template("evaluate_restaurant.html", user_name=user_name, form=form)
    return redirect(url_for("hello"))


@app.route("/restaurant/rate", methods=["GET", "POST"])
def restaurant_rate() -> Union[str, "Response"]:
    form = RateForm(request.form)
    if request.method == "POST":
        user_name = form.user_name.data.strip()
        user = User.get_or_create(user_name)
        restaurant_name = form.restaurant.data.strip()
        restaurant = Restaurant.get_or_create(restaurant_name)
        value = int(form.rate.data)
        Rate.update_or_create(user, restaurant, value)

        return render_template("good_bye.html", user_name=user_name)
    return redirect(url_for("hello"))
