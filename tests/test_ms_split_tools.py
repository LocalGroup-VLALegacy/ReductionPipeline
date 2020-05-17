

def test_continuum_bb_B0D0():

    out = continuum_spws(spw_dict_20A346,
                         baseband='B0D0',
                         return_string=False)

    assert out == list(range(16, 32))

    out = continuum_spws(spw_dict_20A346,
                         baseband='B0D0',
                         return_string=True)

    test_str = ",".join([str(num) for num in list(range(16, 32))])

    assert out == test_str


def test_continuum_bb_A0C0():

    out = continuum_spws(spw_dict_20A346,
                         baseband='A0C0',
                         return_string=False)

    assert out == [0, 4, 8, 11]

    out = continuum_spws(spw_dict_20A346,
                         baseband='A0C0',
                         return_string=True)

    test_str = "0,4,8,11"

    assert out == test_str


def test_continuum_bb_both():

    out = continuum_spws(spw_dict_20A346,
                         baseband='both',
                         return_string=False)

    assert out == [0, 4, 8, 11] + list(range(16, 32))

    out = continuum_spws(spw_dict_20A346,
                         baseband='both',
                         return_string=True)

    test_str = "0,4,8,11," + ",".join([str(num) for num in list(range(16, 32))])

    assert out == test_str


def test_lines_rrls():

    out = line_spws(spw_dict_20A346,
                    include_rrls=True,
                    keep_backup_continuum=False,
                    return_string=False)

    # There's only 4 continuum SPWs in A0
    check_list = list(set(range(0, 16)) - set([0, 4, 8, 11]))

    assert out == check_list

    out = line_spws(spw_dict_20A346,
                    include_rrls=True,
                    keep_backup_continuum=False,
                    return_string=True)

    test_str = ",".join([str(num) for num in check_list])

    assert out == test_str


def test_lines_norrls():

    out = line_spws(spw_dict_20A346,
                    include_rrls=False,
                    keep_backup_continuum=False,
                    return_string=False)

    check_list = [5, 7, 10, 13]
    backups_list = [0, 4, 8, 11]

    check_list += backups_list
    check_list.sort()

    assert out == check_list

    out = line_spws(spw_dict_20A346,
                    include_rrls=False,
                    keep_backup_continuum=False,
                    return_string=True)

    test_str = ",".join([str(num) for num in check_list])

    assert out == test_str


def test_lines_rrls_wbackups():

    out = line_spws(spw_dict_20A346,
                    include_rrls=True,
                    keep_backup_continuum=True,
                    return_string=False)

    # There's only 4 continuum SPWs in A0
    check_list = list(set(range(0, 16)) - set([0, 4, 8, 11]))
    backups_list = [0, 4, 8, 11]

    check_list += backups_list
    check_list.sort()

    assert out == check_list

    out = line_spws(spw_dict_20A346,
                    include_rrls=True,
                    keep_backup_continuum=True,
                    return_string=True)

    test_str = ",".join([str(num) for num in check_list])

    assert out == test_str


def test_lines_norrls_wbackups():

    out = line_spws(spw_dict_20A346,
                    include_rrls=False,
                    keep_backup_continuum=True,
                    return_string=False)

    check_list = [5, 7, 10, 13]
    backups_list = [0, 4, 8, 11]

    check_list += backups_list
    check_list.sort()

    assert out == check_list

    out = line_spws(spw_dict_20A346,
                    include_rrls=False,
                    keep_backup_continuum=True,
                    return_string=True)

    test_str = ",".join([str(num) for num in check_list])

    assert out == test_str
