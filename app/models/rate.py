import logging

import pandas as pd
from sqlalchemy import Column, ForeignKey, Integer, UniqueConstraint
from surprise import SVD, Dataset, NormalPredictor, Reader
from surprise.model_selection import cross_validate

import settings
from app.models.db import BaseDatabase, database
from app.models.restaurant import Restaurant
from app.models.user import User

logger = logging.getLogger(__name__)


class Rate(BaseDatabase):
    __tablename__ = 'rate'
    # CASCADE -> if user data is deleted, this record is deleted at the same time.
    user_id = Column(ForeignKey("user.id", ondelete="CASCADE"))
    restaurant_id = Column(ForeignKey("restaurant.id", ondelete="CASCADE"))
    value = Column(Integer)
    UniqueConstraint(user_id, restaurant_id)

    @staticmethod
    def update_or_create(user: User, restaurant: Restaurant, value: int) -> None:
        session = database.connect_db()
        rate = session.query(Rate).filter(
            Rate.user_id == user.id, Rate.restaurant_id == restaurant.id).first()
        if rate:
            rate.value = value
            session.add(rate)
            session.commit()
            session.close()
            # これがないと下の処理が進み、Insert into エラーが発生してしまうので注意
            return rate

        rate = Rate(user_id=user.id, restaurant_id=restaurant.id, value=value)
        session.add(rate)
        session.commit()
        session.close()

    @staticmethod
    def recommend_restaurant(user: User) -> list:
        """
            Use machine learning to measure recommended restaurants and return the name of the recommend restaurants

            Args:
                user: User object you want to recommend

            Returns: A list of recommended restaurant names
        """
        if not settings.RECOMMEND_ENGINE_ENABLE:
            session = database.connect_db()
            recommend = [r.name for r in session.query(
                Restaurant).all()][:settings.RECCOMEND_RESTAURANT_NUM]
            session.close()
            return recommend

        # -------------------------データ作成
        session = database.connect_db()
        # sql -> pandasのデータフレームに変更
        df = pd.read_sql(
            "SELECT user_id, restaurant_id, value from rate;", session.bind)
        session.close()

        dataset_colums = ["user_id", "restaurant_id", "value"]
        reader = Reader()
        data = Dataset.load_from_df(df[dataset_colums], reader)

        # -------------------------検証
        try:
            # データを評価する
            cross_validate(NormalPredictor(), data, cv=2)
        except ValueError as ex:
            logger.error({"action": "recommend_restaurant", "error": ex})
            return None

        # ------------------------アルゴリズム生成
        # トレーニング
        # 機械学習のアルゴリズム
        svd = SVD()
        trainset = data.build_full_trainset()
        svd.fit(trainset)

        # ------------------------予測
        predict_df = df.copy()
        item_id = "restaurant_id"
        # 新しいカラムを作成
        predict_df["Predicted_Score"] = predict_df[item_id].apply(
            lambda x: svd.predict(user.id, x).est)
        # scoreの良いもの順にsort
        predict_df = predict_df.sort_values(
            by=["Predicted_Score"], ascending=False)
        # 重複データの削除
        predict_df = predict_df.drop_duplicates(subset=item_id)

        if predict_df is None:
            logger.warning({"action": "recommend_restaurant",
                           "status": "no predict data"})
            return []

        # ------------------------結果をリストにして返す
        recommended_restaurants = []
        for i, row in predict_df.iterrows():
            restaurant_id = int(row["restaurant_id"])
            restaurant = Restaurant.get(restaurant_id)
            recommended_restaurants.append(restaurant.name)

        return recommended_restaurants[:settings.RECCOMEND_RESTAURANT_NUM]
