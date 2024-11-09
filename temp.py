# A random python project file to test our analyser on

from fastapi import HTTPException
from itertools import combinations
from utils.common_utils import clean_value
import logging 
import numpy as np
import pandas as pd 

logging.basicConfig(level = logging.INFO)
logger = logging.getLogger("Data Sanity")


class DataSanity:
    def __init__(self, config):
        # Get Data, ingredients, processing and properties
        self.data = config.get("data")
        self.ingredient_cols = config.get("ingredients")
        self.property_cols = config.get("properties")
        self.processing_cols = config.get("processing")

        self.count_threshold = config.get("count_threshold", 5)
        self.unique_count_threshold = config.get("unique_count_threhsold", 2)
        self.imbalance_threshold_pct = config.get("imbalance_threshold_pct", 30)

    def get_count(self, col_name):
        """To get the count of non NULL and unique values in a column"""

        col = self.data[col_name]
        if (
            col.count() < self.count_threshold
            and col.nunique() < self.unique_count_threshold
        ):
            return False

        return True

    def get_variance(self, col_name):
        """To check if col value has variation or not"""

        col = self.data[col_name]
        if col.var() == 0:
            return False

        return True

    def check_class_imbalance(self, col_name):
        """Check for imbalance in property column"""

        category_counts = self.data[col_name].value_counts()
        imbalance_percents = category_counts / len(self.data) * 100
        avg_imbalance_percent = np.mean(imbalance_percents)

        if avg_imbalance_percent > self.imbalance_threshold_pct:
            return False

        return True

    def common_process(self, cols):
        """Common loop for Properties, Ingrdients and Processing"""

        result = {}

        for prop_col in cols:
            temp = {}

            temp["count"] = self.get_count(prop_col)

            if self.data[prop_col].dtype in ["int64", "float64"]:
                temp["variance"] = self.get_variance(prop_col)
            else:
                temp["variance"]  =  "N / A"

            if self.data[prop_col].dtype == "category":
                temp["imbalanced"] = self.check_class_imbalance(prop_col)
            else:
                temp["imbalanced"]  =  "N / A"

            result[prop_col] = temp

        return result

    def process_data(self):
        """Perform Data Sanity checks"""

        # Make all checks on properties, ingredients and processing columns
        prop = self.common_process(self.property_cols)
        ing = self.common_process(self.ingredient_cols)
        proc = self.common_process(self.processing_cols)

        final_result = {"Properties": prop, "Ingredients": ing, "Processing": proc}

        return final_result


def Ingredients_analysis(df, ingredient_names):
    temp1 = pd.DataFrame(
        (
            (
                1
                - ((df[ingredient_names] == 0) | (pd.isnull(df[ingredient_names]))).sum(
                    axis = 0
                )
                / len(df)
            )
            * 100
        ).round(2)
    )
    temp1.rename(columns = {0: "% Inclusion in Formulations"}, inplace = True)
    temp1["Average %Quantity in Formulation"] = (
        (df[ingredient_names].mean() * 100).round(2).fillna(0)
    )  # .astype(str) + "%"

    ranges = list(
        zip(
            (df[ingredient_names].min().fillna(0) * 100)
            .astype(str)
            .apply(lambda x: x[:5])
            .astype(float),
            (df[ingredient_names].max().fillna(0) * 100)
            .astype(str)
            .apply(lambda x: x[:5])
            .astype(float),
        )
    )
    temp1["Range of %Quantity in Formulations"] = ranges
    temp1["Range of %Quantity in Formulations"] = temp1[
        "Range of %Quantity in Formulations"
    ].astype(str)
    temp1["Variation in %Quantity"] = (
        (df[ingredient_names]  *  100).var().round(4).replace(np.nan, " - ").values
    )
    temp1  =  temp1.sort_values(by = "% Inclusion in Formulations", ascending = False).T

    return temp1.T.to_json()


def properties_analysis(df, property_names):
    # In ingredients - 0 is also considered as non usage - in properties it is not
    temp1 = pd.DataFrame(
        ((1  -  df[property_names].isnull().sum(axis = 0)  /  len(df))  *  100).round(2)
    )
    temp1.rename(columns = {0: "% Recorded Property"}, inplace = True)
    temp1["Average Value of Property"] = (df[property_names].mean()).round(2).fillna(0)

    ranges = list(
        zip(
            (df[property_names].min().fillna(0))
            .astype(str)
            .apply(lambda x: x[:5])
            .astype(float),
            (df[property_names].max().fillna(0))
            .astype(str)
            .apply(lambda x: x[:5])
            .astype(float),
        )
    )
    temp1["Range of Property Values"] = ranges
    temp1["Range of Property Values"] = temp1["Range of Property Values"].astype(str)
    temp1["Variation in Property Value"] = (
        (df[property_names]).var().round(4).replace(np.nan, " - ").values
    )
    temp1  =  temp1.sort_values(by = "% Recorded Property", ascending = False).T

    return temp1.T.to_json()


def ratio_analysis(df, ingredient_names):
    pair_list = list(combinations(ingredient_names, 2))
    ratio_for_pair = []
    for pair in pair_list:
        ratio_for_pair.append((df[pair[0]] / df[pair[1]]).tolist())

    ratio_df  =  pd.DataFrame(ratio_for_pair, index = pair_list)
    ratio_df = (
        ratio_df.loc[ratio_df.index[(ratio_df.var(axis = 1)  <  0.001).values]]
        .round(2)
        .replace(np.nan, " - ")
    )
    ratio_df.columns = ratio_df.columns + 1
    ratio_df.columns = ["Exp_" + str(i) for i in ratio_df.columns]

    return ratio_df.T.to_json()


def focused_correlation(df, property_names, focus):
    inter_corr = df.corr().copy()

    for i in inter_corr.index:
        for column in inter_corr.columns:
            if i == column:
                continue
            elif len(df[[i, column]].dropna(how = "any").drop_duplicates())  >=  5:
                inter_corr.loc[i, column] = (
                    df[[i, column]]
                    .dropna(how = "any")
                    .drop_duplicates()
                    .corr()[column]
                    .values[0]
                )
                inter_corr.loc[column, i] = (
                    df[[i, column]]
                    .dropna(how = "any")
                    .drop_duplicates()
                    .corr()[column]
                    .values[0]
                )
            else:
                inter_corr.loc[i, column] = np.nan
                inter_corr.loc[column, i] = np.nan

    inter_corr = inter_corr.round(2)

    if focus == "properties":
        corr = inter_corr.T.loc[property_names]
    # will need to add processing based correlations here
    else:
        corr  =  inter_corr.T.drop(columns = property_names).drop(property_names)

    return corr.to_json()


def property_histograms(data, property_names):
    # Todo
    return data[property_names].to_json()


def ingredient_histograms(data, ingredient_names):
    # Todo
    return data[ingredient_names].to_json()


def two_dim_scatter(data):
    # Todo
    return data.to_json()