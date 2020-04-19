import cb_utils


def test_merge_file():
    filename_in = "../data/to_merge.txt"
    filename_out = "test_merged.txt"
    filename_true = "../data/merged.txt"

    cb_utils.merge_file(filename_in, filename_out)
    with open(filename_out) as fout, open(filename_true) as ftrue:
        assert fout.read() == ftrue.read()
