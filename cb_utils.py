from armetrics import utils as armutils
from armetrics import plotter
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

standardized_names = {"RUMIA PASTURA": "RUMIA", "PASTURA": "PASTOREO", "RUMIA PASTOREO": "RUMIA",
                      "RUMIA EN PASTURA": "RUMIA", "GRAZING": "PASTOREO", "RUMINATION": "RUMIA",
                      "R": "RUMIA", "P": "PASTOREO"}
segmentation_replacements = {"RUMIA": "SEGMENTACION", "PASTOREO": "SEGMENTACION", "REGULAR": "SEGMENTACION"}
_names_of_interest = ["PASTOREO", "RUMIA"]


def load_chewbite(filename, start=None, end=None, verbose=True, to_segmentation=False):
    df = pd.read_table(filename, decimal=',', header=None, delim_whitespace=True, 
                       names=["bl_start", "bl_end", "label"], usecols=[0, 1, 2])

    df[["bl_start", "bl_end"]] = df[["bl_start", "bl_end"]].astype('float')

    df = df.round(0)
    df.label = df.label.str.strip().str.upper()
    df.label.replace(standardized_names, inplace=True)
    df[["bl_start", "bl_end"]] = df[["bl_start", "bl_end"]].astype('int')

    # It will modify the limits of partially selected labels
    # Given end and start may be in the middle of a label
    if start:
        df = df[df.bl_end > start]
        df.loc[df.bl_start < start, "bl_start"] = start
        df = df[df.bl_start >= start]
    if end:
        df = df[df.bl_start < end]
        df.loc[df.bl_end > end, "bl_end"] = end
        df = df[df.bl_end <= end]
    names_of_interest = _names_of_interest
    if to_segmentation:
        names_of_interest = ["SEGMENTACION"]
        df.label.replace(segmentation_replacements, inplace=True)
    if verbose:
        print("Labels in (", start, ",", end, ") from", filename, "\n", df.label.unique())

    df = df.loc[df.label.isin(names_of_interest)]

    segments = [armutils.Segment(bl_start, bl_end, label) for name, (bl_start, bl_end, label) in df.iterrows()]
    indexes = [np.arange(bl_start, bl_end) for name, (bl_start, bl_end, label) in df.iterrows()]
    if len(segments) < 1:
        print("Warning, you are trying to load a span with no labels from:", filename)
        indexes = [np.array([])]  # To avoid errors when no blocks are present in the given interval

    frames = armutils.segments2frames(segments)
    indexes = np.concatenate(indexes)

    s = pd.Series(frames, index=indexes)

    if s.index.has_duplicates:
        print("Overlapping labels were found in", filename)
        print("Check labels corresponding to times given below (in seconds):")
        print(s.index[s.index.duplicated()])

    if len(segments) < 1:
        series_len = 1  # Provides a series with a single element that has an empty label, to avoid error
    else:
        series_len = s.index[-1]  # The series will have the length of up to the last second of the last block

    s_formatted = s.reindex(np.arange(series_len), fill_value="")

    return s_formatted


def length_signal_chewbite(filename, start=None, end=None, verbose=True, to_segmentation=False):
    df = pd.read_table(filename, decimal=',', header=None)
    df.dropna(axis=1, how='all', inplace=True)
    df.columns = ["start", "end", "label"]

    df[["start", "end"]] = df[["start", "end"]].astype('float')

    df = df.round(0)
    df[["start", "end"]] = df[["start", "end"]].astype('int')

    # It will modify the limits of partially selected labels
    # Given end and start may be in the middle of a label
    if start:
        df = df[df.end > start]
        df.loc[df.start < start, "start"] = start
        df = df[df.start >= start]
    if end:
        df = df[df.start < end]
        df.loc[df.end > end, "end"] = end
        df = df[df.end <= end]

    return df["end"].max() - df["start"].min()


def merge_contiguous(df):
    """ Given a dataframe df with start, end and label columns it will merge contiguous equally labeled """
    for i in df.index[:-1]:
        next_label = df.loc[i + 1].label
        if next_label == df.loc[i].label:
            df.loc[i + 1, "start"] = df.loc[i].start
            df.drop(i, inplace=True)
    return df


def remove_silences(filename_in, filename_out, max_len=300, sil_label="SILENCIO"):
    """ Given a labels filename will remove SILENCE blocks shorter than max_len (in seconds)
        if they are surrounded by blocks with the same label.
        This silences will be merged with contiguous blocks.
    """
    df = pd.read_table(filename_in, decimal=',', header=None)
    df.dropna(axis=1, how='all', inplace=True)
    df.columns = ["start", "end", "label"]

    df[["start", "end"]] = df[["start", "end"]].astype('float')
    df = df.round(0)
    df.label = df.label.str.strip().str.upper()
    df[["start", "end"]] = df[["start", "end"]].astype('int')
    
    sil_label = str.strip(str.upper(sil_label))

    for i, (start, end, label) in df.loc[df.index[1:-1]].iterrows():
        length = end - start
        prev_label = df.loc[i - 1].label
        next_label = df.loc[i + 1].label
        if label == sil_label and length <= max_len and prev_label == next_label:
            df.loc[i, "label"] = prev_label

    df = merge_contiguous(df)

    df.to_csv(filename_out,
              header=False, index=False, sep="\t")


def remove_between_given(filename_in, filename_out, search_label, max_len=300):
    """ Given a labels filename will remove blocks shorter than max_len (in seconds)
        if they are surrounded by blocks of the search_label.
        This short blocks will be merged with contiguous blocks.
    """
    df = pd.read_table(filename_in, decimal=',', header=None)
    df.dropna(axis=1, how='all', inplace=True)
    df.columns = ["start", "end", "label"]

    df[["start", "end"]] = df[["start", "end"]].astype('float')
    df = df.round(0)
    df.label = df.label.str.strip().str.upper()
    df[["start", "end"]] = df[["start", "end"]].astype('int')

    for i, (start, end, label) in df.loc[df.index[1:-1]].iterrows():
        length = end - start
        prev_label = df.loc[i - 1].label
        next_label = df.loc[i + 1].label
        if label != search_label and length <= max_len \
                and next_label == prev_label == search_label:
            df.loc[i, "label"] = search_label

    df = merge_contiguous(df)

    df.to_csv(filename_out,
              header=False, index=False, sep="\t")


def merge_file(filename_in, filename_out):
    """
    Given a labels filename_in will merge contiguous blocks and save it to filename_out.
    """
    df = pd.read_table(filename_in, decimal=',', header=None)
    df.dropna(axis=1, how='all', inplace=True)
    df.columns = ["start", "end", "label"]

    df[["start", "end"]] = df[["start", "end"]].astype('float')
    df = df.round(0)
    df.label = df.label.str.strip().str.upper()
    df[["start", "end"]] = df[["start", "end"]].astype('int')

    df = merge_contiguous(df)

    df.to_csv(filename_out,
              header=False, index=False, sep="\t")


def violinplot_metric_from_report(single_activity_report, metric):
    grouped_reports = single_activity_report.groupby("predictor_name")
    n_predictors = len(grouped_reports)
    predictors_labels = []
    activity = single_activity_report.activity.iloc[0]

    plt.figure()
    pos = np.arange(n_predictors) + .5  # the bar centers on the y axis

    if n_predictors > 10:
        print("Be careful! I cannot plot more than 10 labels.")
    # colors = ["C%d" % i for i in range(n_predictors)]

    for (predictor_name, predictor_report), p in zip(grouped_reports, pos):
        predictors_labels.append(predictor_name)

        values_to_plot = predictor_report.loc[:, metric].values
        plt.violinplot(values_to_plot[np.isfinite(values_to_plot)], [p], points=50, vert=False, widths=0.65,
                       showmeans=False, showmedians=True, showextrema=True, bw_method='silverman')

    plt.axvline(x=0, color="k", linestyle="dashed")
    plt.axvline(x=1, color="k", linestyle="dashed")
    plt.yticks(pos, predictors_labels)
    plt.gca().invert_yaxis()
    plt.minorticks_on()
    plt.xlabel('Frame F1-score')

    plt.tight_layout()
    plt.savefig('violin_' + metric + "_" + activity + '.pdf')
    plt.savefig('violin_' + metric + "_" + activity + '.png')
    plt.show()


def my_display_report(complete_report_df):
    report_activity_grouped = complete_report_df.groupby("activity")
    
    for activity_label, single_activity_report in report_activity_grouped:
        print("\n================", activity_label, "================\n")
        violinplot_metric_from_report(single_activity_report, "frame_f1score")