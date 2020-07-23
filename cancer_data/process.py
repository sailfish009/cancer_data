from config import DOWNLOAD_DIR, PROCESSED_DIR, SCHEMA

import os

import math
import numpy as np
import pandas as pd

from utils import bcolors, file_exists, export_hdf

from gtfparse import read_gtf

from collections import defaultdict


def check_dependencies(dependencies):

    if dependencies is None or dependencies != dependencies:
        return

    for d in dependencies.split(","):

        d_file = f"{PROCESSED_DIR}/{d}.h5"

        assert file_exists(d_file), f"Dependency {d} does not exist."


def parentheses_to_snake(x):
    x_split = x.split(" (")
    return f"{x_split[0]}_{x_split[1][:-1]}"


class Processors:
    def __init__(self):
        return

    def g19_7_definitions(raw_path, output_id):
        df = read_gtf(raw_path)

        export_hdf(output_id, df)

    def ensembl_75_definitions(raw_path, output_id):
        df = read_gtf(raw_path)

        export_hdf(output_id, df)

    def gtex_2919_manifest(raw_path, output_id):
        df = pd.read_csv(raw_path, sep="\t")

        export_hdf(output_id, df)

    def gtex_5214_manifest(raw_path, output_id):
        df = pd.read_csv(raw_path, sep="\t")

        export_hdf(output_id, df)

    def gtex_manifest(raw_path, output_id):

        gtex_manifest_1 = pd.read_hdf(f"{PROCESSED_DIR}/gtex_2919_manifest.h5")
        gtex_manifest_2 = pd.read_hdf(f"{PROCESSED_DIR}/gtex_5214_manifest.h5")

        gtex_manifest = pd.concat([gtex_manifest_1, gtex_manifest_2], axis=0, sort=True)

        gtex_manifest = gtex_manifest.astype(str)

        export_hdf(output_id, gtex_manifest)

    def gtex_gene_tpm(raw_path, output_id):
        df = pd.read_csv(raw_path, skiprows=2, index_col=0, sep="\t")

        df.index = df["Description"] + "_" + df.index
        df.drop(["Description"], axis=1, inplace=True)
        df = df.T
        df = np.log2(df + 1)

        df = df.astype(np.float16)

        export_hdf(output_id, df)

    # TODO: GTEx splicing

    def ccle_annotations(raw_path, output_id):

        df = pd.read_csv(raw_path, sep="\t")
        df = df.astype(str)

        export_hdf(output_id, df)

    def ccle_translocations_svaba(raw_path, output_id):

        df = pd.read_excel(raw_path)

        ccle_annotations = pd.read_hdf(f"{PROCESSED_DIR}/ccle_annotations.h5")
        ccle_to_depmap = dict(
            zip(ccle_annotations["CCLE_ID"], ccle_annotations["depMapID"])
        )

        string_cols = [
            "CCLE_name",
            "map_id",
            "bp1",
            "bp2",
            "class",
            "gene1",
            "gene2",
            "site1",
            "site2",
            "fusion",
        ]

        for col in string_cols:
            df[col] = df[col].astype(str)

        df["depmap_id"] = df["CCLE_name"].apply(ccle_to_depmap.get)

        export_hdf(output_id, df)

    def ccle_rppa_info(raw_path, output_id):

        df = pd.read_csv(raw_path)
        df = df.astype(str)

        df["format_id"] = (
            df["Target_Genes"].apply(lambda x: x.replace(" ", "-"))
            + "_"
            + df["Antibody_Name"]
        )

        export_hdf(output_id, df)

    def ccle_rppa(raw_path, output_id):

        df = pd.read_csv(raw_path, index_col=0)

        ccle_rppa_info = pd.read_hdf(f"{PROCESSED_DIR}/ccle_rppa_info.h5")
        antibody_name_map = dict(
            zip(ccle_rppa_info["Antibody_Name"], ccle_rppa_info["format_id"])
        )

        ccle_annotations = pd.read_hdf(f"{PROCESSED_DIR}/ccle_annotations.h5")
        ccle_to_depmap = dict(
            zip(ccle_annotations["CCLE_ID"], ccle_annotations["depMapID"])
        )

        df.columns = map(antibody_name_map.get, df.columns)
        df.index = df.index.map(ccle_to_depmap.get)

        export_hdf(output_id, df)

    def ccle_gene_tpm(raw_path, output_id):

        df = pd.read_csv(raw_path, sep="\t", index_col=0)
        df = df.iloc[:, 1:]

        g19_7_definitions = pd.read_hdf(f"{PROCESSED_DIR}/g19_7_definitions.h5")

        gene_name_map = dict(
            zip(g19_7_definitions["gene_id"], g19_7_definitions["gene_name"])
        )
        gene_name_map = defaultdict(str, gene_name_map)

        gene_names = df.index.map(lambda x: f"{gene_name_map.get(x)}_{x}")

        df = df.set_index(gene_names)
        df = np.log2(df + 1)
        df = df.astype(np.float16)

        df = df.T

        ccle_annotations = pd.read_hdf(f"{PROCESSED_DIR}/ccle_annotations.h5")
        ccle_to_depmap = dict(
            zip(ccle_annotations["CCLE_ID"], ccle_annotations["depMapID"])
        )

        df.index = df.index.map(ccle_to_depmap.get)

        export_hdf(output_id, df)

    def ccle_transcript_tpm(raw_path, output_id):

        df = pd.read_csv(raw_path, sep="\t")

        g19_7_definitions = pd.read_hdf(f"{PROCESSED_DIR}/g19_7_definitions.h5")

        gene_name_map = dict(
            zip(g19_7_definitions["gene_id"], g19_7_definitions["gene_name"])
        )
        gene_name_map = defaultdict(str, gene_name_map)

        df.index = df[["gene_id", "transcript_id"]].apply(
            lambda x: f"{gene_name_map.get(x['gene_id'])}_{x['transcript_id']}", axis=1
        )

        df = df.drop(["gene_id", "transcript_id"], axis=1)

        df = np.log2(df + 1)
        df = df.astype(np.float16)
        df = df.T

        ccle_annotations = pd.read_hdf(f"{PROCESSED_DIR}/ccle_annotations.h5")
        ccle_to_depmap = dict(
            zip(ccle_annotations["CCLE_ID"], ccle_annotations["depMapID"])
        )

        df.index = df.index.map(ccle_to_depmap.get)

        export_hdf(output_id, df)

    # TODO: CCLE exonusage

    def ccle_mirna(raw_path, output_id):

        df = pd.read_csv(raw_path, sep="\t", skiprows=2)

        df.index = df["Description"] + "_" + df["Name"].apply(lambda x: x[1:])

        df = df.iloc[:, 2:]
        df = np.log2(df)
        df = df.T
        df = df.astype(np.float16)

        ccle_annotations = pd.read_hdf(f"{PROCESSED_DIR}/ccle_annotations.h5")
        ccle_to_depmap = dict(
            zip(ccle_annotations["CCLE_ID"], ccle_annotations["depMapID"])
        )

        df.index = df.index.map(ccle_to_depmap.get)

        export_hdf(output_id, df)

    def ccle_rrbs_tss1kb(raw_path, output_id):

        df = pd.read_csv(raw_path, sep="\t", index_col=0)
        df = df.iloc[:-1, 2:]
        df = df.T

        df[df == "\tNA"] = np.nan
        df[df == "    NA"] = np.nan
        df[df == "     NA"] = np.nan
        df = df.astype(np.float16)

        ccle_annotations = pd.read_hdf(f"{PROCESSED_DIR}/ccle_annotations.h5")
        ccle_to_depmap = dict(
            zip(ccle_annotations["CCLE_ID"], ccle_annotations["depMapID"])
        )

        df.index = df.index.map(ccle_to_depmap.get)

        export_hdf(output_id, df)

    def ccle_rrbs_tss_clusters(raw_path, output_id):

        df = pd.read_csv(raw_path, sep="\t", index_col=0)
        df = df.iloc[:-1, 2:]
        df = df.T

        df[df == "\tNA"] = np.nan
        df[df == "    NA"] = np.nan
        df[df == "     NA"] = np.nan
        df = df.astype(np.float16)

        ccle_annotations = pd.read_hdf(f"{PROCESSED_DIR}/ccle_annotations.h5")
        ccle_to_depmap = dict(
            zip(ccle_annotations["CCLE_ID"], ccle_annotations["depMapID"])
        )

        df.index = df.index.map(ccle_to_depmap.get)

        export_hdf(output_id, df)

    def ccle_rrbs_cgi_clusters(raw_path, output_id):

        df = pd.read_csv(raw_path, sep="\t", index_col=0)
        df = df.iloc[:-1]

        df["cluster_pos"] = df.index
        df["cluster_n"] = df.groupby("cluster_pos").cumcount() + 1
        df.index = df["cluster_pos"].astype(str) + "-" + df["cluster_n"].astype(str)

        df = df.iloc[:, 2:-2]
        df = df.T

        df[df == "\tNA"] = np.nan
        df[df == "    NA"] = np.nan
        df[df == "     NA"] = np.nan
        df = df.astype(np.float16)

        ccle_annotations = pd.read_hdf(f"{PROCESSED_DIR}/ccle_annotations.h5")
        ccle_to_depmap = dict(
            zip(ccle_annotations["CCLE_ID"], ccle_annotations["depMapID"])
        )

        df.index = df.index.map(ccle_to_depmap.get)

        export_hdf(output_id, df)

    def ccle_rrbs_enhancer_clusters(raw_path, output_id):

        df = pd.read_csv(raw_path, sep="\t", index_col=0)

        df.index = df.index + "_" + df.groupby(level=0).cumcount().astype(str)

        df = df.iloc[:, 2:]
        df.index = df.index.map(lambda x: x.replace("_", "-")) + "_enh"
        df = df.T

        df[df == "\tNA"] = np.nan
        df[df == "    NA"] = np.nan
        df[df == "     NA"] = np.nan
        df = df.astype(np.float16)

        ccle_annotations = pd.read_hdf(f"{PROCESSED_DIR}/ccle_annotations.h5")
        ccle_to_depmap = dict(
            zip(ccle_annotations["CCLE_ID"], ccle_annotations["depMapID"])
        )

        df.index = df.index.map(ccle_to_depmap.get)

        export_hdf(output_id, df)

    def ccle_tertp(raw_path, output_id):

        df = pd.read_excel(raw_path, skiprows=4)

        df = df.set_index("depMapID")
        df["TERTp_mut"] = df["TERT_promoter_mutation"] != "wildtype"

        export_hdf(output_id, df)

    def ccle_msi(raw_path, output_id):

        df = pd.read_excel(raw_path, sheet_name="MSI calls")

        df = df[df["CCLE.MSI.call"].isin(["inferred-MSI", "inferred-MSS"])]

        df = df.astype(str)

        df["MSI"] = df["CCLE.MSI.call"] == "inferred-MSI"

        df = df.set_index("depMapID")

        export_hdf(output_id, df)

    def ccle_metabolomics(raw_path, output_id):

        df = pd.read_csv(raw_path)

        df["DepMap_ID"] = df["DepMap_ID"].astype(str)

        df = df.set_index("DepMap_ID")
        df = df.drop(["CCLE_ID"], axis=1)

        df = df.astype(np.float16)

        export_hdf(output_id, df)

    def depmap_annotations(raw_path, output_id):

        df = pd.read_csv(raw_path, index_col=0)

        df["display_disease"] = df["lineage"].apply(
            lambda x: x.replace("_", " ").capitalize()
        )
        df["display_disease"] = df["display_disease"].apply(
            lambda x: "Unknown" if x == " " else x
        )

        df = df.astype(str)

        export_hdf(output_id, df)

    def avana(raw_path, output_id):

        df = pd.read_csv(raw_path, index_col=0)

        df.columns = map(parentheses_to_snake, df.columns)

        df = df.astype(np.float16)

        export_hdf(output_id, df)

    def drive(raw_path, output_id):

        df = pd.read_csv(raw_path, index_col=0)

        depmap_annotations = pd.read_hdf(f"{PROCESSED_DIR}/depmap_annotations.h5")
        ccle_to_depmap = dict(
            zip(depmap_annotations["CCLE_Name"], depmap_annotations.index)
        )

        df.columns = map(ccle_to_depmap.get, df.columns)
        df.index = df.index.map(parentheses_to_snake)

        df.columns = df.columns.astype(str)
        df.index = df.index.astype(str)

        df = df.T
        df = df.astype(np.float16)

        export_hdf(output_id, df)

    def achilles(raw_path, output_id):

        df = pd.read_csv(raw_path, index_col=0)

        depmap_annotations = pd.read_hdf(f"{PROCESSED_DIR}/depmap_annotations.h5")
        ccle_to_depmap = dict(
            zip(depmap_annotations["CCLE_Name"], depmap_annotations.index)
        )

        df.columns = map(ccle_to_depmap.get, df.columns)
        df.index = df.index.map(parentheses_to_snake)

        df.columns = df.columns.astype(str)
        df.index = df.index.astype(str)

        df = df.T
        df = df.astype(np.float16)

        export_hdf(output_id, df)

    def depmap_gene_tpm(raw_path, output_id):

        df = pd.read_csv(raw_path, index_col=0)
        df.columns = map(parentheses_to_snake, df.columns)

        df = df.astype(np.float16)

        export_hdf(output_id, df)

    # TODO: DepMap mutations

    def prism_primary_info(raw_path, output_id):

        df = pd.read_csv(raw_path)

        df["format_name"] = df["name"].fillna("UNNAMED") + "_" + df["column_name"]
        df = df.astype(str)

        export_hdf(output_id, df)

    def prism_primary_logfold(raw_path, output_id):

        df = pd.read_csv(raw_path, index_col=0)

        prism_primary_info = pd.read_hdf(f"{PROCESSED_DIR}/prism_primary_info.h5")
        primary_name_map = dict(
            zip(prism_primary_info["column_name"], prism_primary_info["format_name"])
        )

        df.columns = map(primary_name_map.get, df.columns)

        df = df.astype(np.float16)

        export_hdf(output_id, df)

    def prism_secondary_info(raw_path, output_id):

        df = pd.read_csv(raw_path)

        df["format_name"] = df["name"].fillna("UNNAMED") + "_" + df["column_name"]
        df = df.astype(str)

        export_hdf(output_id, df)


if __name__ == "__main__":

    for _, file in SCHEMA.iterrows():

        if file["type"] in ["primary_dataset", "secondary_dataset"]:

            output_path = f"{PROCESSED_DIR}/{file['id']}.h5"

            if file_exists(output_path):

                print(
                    f"{bcolors.BOLD}{file['id']}{bcolors.ENDC} already processed, skipping"
                )

            else:

                handler = getattr(Processors, file["id"], None)

                if handler is not None:

                    print(f"Processing {bcolors.BOLD}{file['id']}{bcolors.ENDC}")

                    check_dependencies(file["dependencies"])

                    handler(f"{DOWNLOAD_DIR}/{file['downloaded_name']}", file["id"])
