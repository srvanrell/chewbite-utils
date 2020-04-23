import pandas as pd
import chewbite_utils


def test_merge_file():
    filename_in = "../data/to_merge.txt"
    filename_out = "test_merged.txt"
    filename_true = "../data/merged.txt"

    chewbite_utils.merge_file(filename_in, filename_out)
    with open(filename_out) as fout, open(filename_true) as ftrue:
        assert fout.read() == ftrue.read()


def test_load_chewbite2():
    filename_in = "../data/simple_int_2labels.txt"
    df_true = pd.DataFrame({"start": [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0],
                            "end": [3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0],
                            "label": ["", "RUMIA", "", "PASTOREO", "PASTOREO", "", ""]})
    df_out = chewbite_utils.load_chewbite2(filename_in, frame_len=3)

    assert df_true.equals(df_out)


def test_load_chewbite2_long_frame():
    filename_in = "../data/simple_frame5_with_2labels.txt"
    df_true = pd.DataFrame({"start": [0.0, 5.0, 10.0, 15.0, 20.0],
                            "end": [5.0, 10.0, 15.0, 20.0, 25.0],
                            "label": ["RUMIA", "RUMIA", "", "", ""]})
    df_out = chewbite_utils.load_chewbite2(filename_in, frame_len=5)

    assert df_true.equals(df_out)


def test_load_chewbite2_float_long_frame():
    filename_in = "../data/simple_float_2labels.txt"
    df_true = pd.DataFrame({"start": [0.0, 3.5, 7.0, 10.5, 14.0, 17.5],
                            "end": [3.5, 7.0, 10.5, 14.0, 17.5, 21.0],
                            "label": ["", "RUMIA", "", "PASTOREO", "PASTOREO", ""]})
    df_out = chewbite_utils.load_chewbite2(filename_in, frame_len=3.5, decimals=1)

    assert df_true.equals(df_out)


def test_load_chewbite2_no_labels():
    filename_in = "../data/simple_nolabels.txt"
    df_true = pd.DataFrame({"start": [0.0, 10.0, 20.0, 30.0],
                            "end": [10.0, 20.0, 30.0, 40.0],
                            "label": ["", "", "", ""]})
    df_out = chewbite_utils.load_chewbite2(filename_in, frame_len=10, decimals=1)

    assert df_true.equals(df_out)


def test_load_chewbite2_start_end_long_frame():
    filename_in = "../data/simple_float_2labels.txt"
    df_true = pd.DataFrame({"start": [8.0, 11.5, 15.0],
                            "end": [11.5, 15.0, 18.5],
                            "label": ["", "PASTOREO", ""]})
    df_out = chewbite_utils.load_chewbite2(filename_in, start=8, end=17.0, frame_len=3.5, decimals=1)

    assert df_true.equals(df_out)
