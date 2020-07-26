from collections import Counter

import numpy as np
import pandas as pd

from ..access import Datasets
from ..utils import parentheses_to_snake


# minimum mutation frequency for depmap_damaging()
# and depmap_hotspot()
MIN_COUNT_CUTOFF = 4


class Processors:
    """

    DepMap dataset processors.

    """

    @staticmethod
    def depmap_annotations(raw_path):
        """

        Process DepMap cell line annotations.

        Args:
            raw_path (str): the complete path to the
                            raw downloaded file

        Returns:
            Processed DataFrame

        """

        df = pd.read_csv(raw_path, index_col=0)

        df["display_disease"] = df["lineage"].apply(
            lambda x: x.replace("_", " ").capitalize()
        )
        df["display_disease"] = df["display_disease"].apply(
            lambda x: "Unknown" if x == " " else x
        )

        df = df.astype(str)

        return df

    @staticmethod
    def avana(raw_path):
        """

        Process DepMap Avana sensitivities.

        Args:
            raw_path (str): the complete path to the
                            raw downloaded file

        Returns:
            Processed DataFrame

        """

        df = pd.read_csv(raw_path, index_col=0)

        df.columns = map(parentheses_to_snake, df.columns)

        df = df.astype(np.float16)

        return df

    @staticmethod
    def drive(raw_path):
        """

        Process DepMap DRIVE sensitivities.

        Args:
            raw_path (str): the complete path to the
                            raw downloaded file

        Returns:
            Processed DataFrame

        """

        df = pd.read_csv(raw_path, index_col=0)

        depmap_annotations = Datasets.load("depmap_annotations")
        ccle_to_depmap = dict(
            zip(depmap_annotations["CCLE_Name"], depmap_annotations.index)
        )

        df.columns = map(ccle_to_depmap.get, df.columns)
        df.index = df.index.map(parentheses_to_snake)

        df.columns = df.columns.astype(str)
        df.index = df.index.astype(str)

        df = df.T
        df = df.astype(np.float16)

        return df

    @staticmethod
    def achilles(raw_path):
        """

        Process DepMap Achilles sensitivities.

        Args:
            raw_path (str): the complete path to the
                            raw downloaded file

        Returns:
            Processed DataFrame

        """

        df = pd.read_csv(raw_path, index_col=0)

        depmap_annotations = Datasets.load("depmap_annotations")
        ccle_to_depmap = dict(
            zip(depmap_annotations["CCLE_Name"], depmap_annotations.index)
        )

        df.columns = map(ccle_to_depmap.get, df.columns)
        df.index = df.index.map(parentheses_to_snake)

        df.columns = df.columns.astype(str)
        df.index = df.index.astype(str)

        df = df.T
        df = df.astype(np.float16)

        return df

    @staticmethod
    def depmap_gene_tpm(raw_path):
        """

        Process DepMap gene TPM estimates.

        Args:
            raw_path (str): the complete path to the
                            raw downloaded file

        Returns:
            Processed DataFrame

        """

        df = pd.read_csv(raw_path, index_col=0)
        df.columns = map(parentheses_to_snake, df.columns)

        df = df.astype(np.float16)

        return df

    @staticmethod
    def depmap_mutations(raw_path):
        """

        Process DepMap mutation calls.

        Args:
            raw_path (str): the complete path to the
                            raw downloaded file

        Returns:
            Processed DataFrame

        """

        df = pd.read_csv(raw_path, sep="\t")

        df = df.astype(str)

        df["Start_position"] = df["Start_position"].astype(int)
        df["End_position"] = df["End_position"].astype(int)

        return df

    @staticmethod
    def depmap_damaging():
        """

        Construct binary mutation matrix for 
        DepMap damaging mutations.

        Returns:
            Processed DataFrame

        """

        df = Datasets.load("depmap_mutations")

        df = df[df["Variant_annotation"] == "damaging"]

        # exclude rarely damaged genes
        mut_counts = Counter(df["Hugo_Symbol"])
        df["count"] = df["Hugo_Symbol"].apply(mut_counts.get)
        df = df[df["count"] >= MIN_COUNT_CUTOFF]

        # remove damaged duplicates
        df["id"] = df["Hugo_Symbol"] + "_" + df["DepMap_ID"]
        df = df.drop_duplicates(subset=["id"], keep="first")

        # dummy value for pivot table
        df["value"] = 1

        mut_mat = pd.pivot_table(
            df, values="value", index=["DepMap_ID"], columns="Hugo_Symbol", fill_value=0
        )

        mut_mat = mut_mat.astype(bool)

        return mut_mat

    @staticmethod
    def depmap_hotspot():
        """

        Construct binary mutation matrix for 
        DepMap hotspot mutations.

        Returns:
            Processed DataFrame

        """

        df = Datasets.load("depmap_mutations")

        df = df[(df["isCOSMIChotspot"] == True) | (df["isTCGAhotspot"] == True)]

        # exclude rarely damaged genes
        mut_counts = Counter(df["Hugo_Symbol"])
        df["count"] = df["Hugo_Symbol"].apply(mut_counts.get)
        df = df[df["count"] >= MIN_COUNT_CUTOFF]

        # remove damaged duplicates
        df["id"] = df["Hugo_Symbol"] + "_" + df["DepMap_ID"]
        df = df.drop_duplicates(subset=["id"], keep="first")

        # dummy value for pivot table
        df["value"] = 1

        mut_mat = pd.pivot_table(
            df, values="value", index=["DepMap_ID"], columns="Hugo_Symbol", fill_value=0
        )

        mut_mat = mut_mat.astype(bool)

        return mut_mat

    @staticmethod
    def prism_primary_info(raw_path):
        """

        Process PRISM primary screen drug metadata.

        Args:
            raw_path (str): the complete path to the
                            raw downloaded file

        Returns:
            Processed DataFrame

        """

        df = pd.read_csv(raw_path)

        df["format_name"] = df["name"].fillna("UNNAMED") + "_" + df["column_name"]
        df = df.astype(str)

        return df

    @staticmethod
    def prism_primary_logfold(raw_path):
        """

        Process PRISM primary screen sensitivities.

        Args:
            raw_path (str): the complete path to the
                            raw downloaded file

        Returns:
            Processed DataFrame

        """

        df = pd.read_csv(raw_path, index_col=0)

        prism_primary_info = Datasets.load("prism_primary_info")
        primary_name_map = dict(
            zip(prism_primary_info["column_name"], prism_primary_info["format_name"])
        )

        df.columns = map(primary_name_map.get, df.columns)

        df = df.astype(np.float16)

        return df

    @staticmethod
    def prism_secondary_info(raw_path):
        """

        Process PRISM secondary screen drug metadata.

        Args:
            raw_path (str): the complete path to the
                            raw downloaded file

        Returns:
            Processed DataFrame

        """

        df = pd.read_csv(raw_path)

        df["format_name"] = df["name"].fillna("UNNAMED") + "_" + df["column_name"]
        df = df.astype(str)

        return df

    @staticmethod
    def prism_secondary_logfold(raw_path):
        """

        Process PRISM secondary screen sensitivities.

        Args:
            raw_path (str): the complete path to the
                            raw downloaded file

        Returns:
            Processed DataFrame

        """

        df = pd.read_csv(raw_path, index_col=0)

        prism_secondary_info = Datasets.load("prism_secondary_info")
        primary_name_map = dict(
            zip(
                prism_secondary_info["column_name"], prism_secondary_info["format_name"]
            )
        )

        df.columns = map(primary_name_map.get, df.columns)

        df = df.astype(np.float16)

        return df

    @staticmethod
    def depmap_copy_number(raw_path):
        """

        Process DepMap copy number estimates.

        Args:
            raw_path (str): the complete path to the
                            raw downloaded file

        Returns:
            Processed DataFrame

        """

        df = pd.read_csv(raw_path, index_col=0)
        df.columns = map(parentheses_to_snake, df.columns)

        df = df.astype(np.float16)

        return df
