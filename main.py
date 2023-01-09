import pandas as pd
import openpyxl
import numpy as np


def manage_custom_rows(df):
    # Adding all formación general valórica not existent in current dataframe
    df = df.append({'MATERIA_CURSO': 'fgv-001', 'TITULO': 'formación general valórica i', 'CRÉDITO': 1000},
                   ignore_index=True)
    df = df.append({'MATERIA_CURSO': 'fgv-002', 'TITULO': 'formación general valórica ii', 'CRÉDITO': 2000},
                   ignore_index=True)
    df = df.append({'MATERIA_CURSO': 'fgv-003', 'TITULO': 'formación general valórica iii', 'CRÉDITO': 2000},
                   ignore_index=True)
    df = df.append({'MATERIA_CURSO': 'fgv-004', 'TITULO': 'formación general valórica iv', 'CRÉDITO': 2000},
                   ignore_index=True)
    # Adding all formación general electiva not existent in current dataframe
    df = df.append({'MATERIA_CURSO': 'fge-001', 'TITULO': 'formación general electiva i', 'CRÉDITO': 2000},
                   ignore_index=True)
    df = df.append({'MATERIA_CURSO': 'fge-002', 'TITULO': 'formación general electiva ii', 'CRÉDITO': 2000},
                   ignore_index=True)

    old_values = ['nivelación inglés a',
                  'nivelación inglés b',
                  'pr. introducción a la ing ii',
                  'pr. intro. a la ingeniería',
                  'arquitectura y org. de computa',
                  'pr. ciencias aplicadas',
                  'diseño y análisis de algoritmo',
                  'pr. proces. analítico de datos',
                  'pr. des. soft. bas. en plataf.',
                  'pr. tópicos avanzados de i.s',
                  'pr. dis. de sist. de int. de n']
    new_values = ['inglés nivelación a',
                  'inglés nivelación b',
                  'proyecto introducción a la ingeniería ii',
                  'proyecto introducción a la ingeniería i',
                  'arquitectura y organización de computadores',
                  'proyecto ciencias aplicadas',
                  'diseño y análisis de algoritmos',
                  'proyecto procesamiento analítico de datos',
                  'proyecto desarrollo software basado en plataformas',
                  'proyecto tópicos avanzados de ingeniería de software',
                  'proyecto diseño de sistemas de inteligencia de negocios']

    df['TITULO'] = df['TITULO'].replace(old_values, new_values)
    return df


def extract_transform_load(df1, df2):
    # 'oferta1' are the courses in 1st semester
    # 'oferta2' are the courses in 2nd semester
    # some courses exists in both, other courses not
    df = pd.concat([df1, df2])
    # Set headers to upper case
    df.columns = [x.upper() for x in df.columns]
    # Drop all columns except the columns we need
    df = df[['MATERIA_CURSO', 'TITULO', 'CRÉDITO']]

    # drop all name courses duplicates, we only need one instance
    # NCR are different in the same courses, the department-id code are the same for all
    df = df.drop_duplicates(subset=['TITULO'])
    # the values in 'credit' column are single digits (or 30 for capstone project)
    # this is not a problem, but for own purposes I prefer to amplify by 1000
    df = df.applymap(lambda s: s * 1000 if type(s) == int else s.lower())
    # replace elements with different names but existents
    df = manage_custom_rows(df)
    with pd.ExcelWriter('output.xlsx') as writer:
        df.to_excel(writer, sheet_name='oferta_simplificada', index=False)
    return df


def get_buttons(df):
    # Create html base code for buttons
    with open("buttons.txt", "w") as f:
        for index, row in df.iterrows():
            text = '<button class="btn btn-coutb-gray" id="' + str(row[0]) + '">' + str(row[1]) + '</button>'
            f.write(text + "\n")
    # there's no .close() needed because this way with writer close automatically


def create_pre_requisites_dict(df):
    pre_requisites = dict()
    with open('relaciones.txt', encoding='utf8') as f:
        for line in f:
            line = line.strip().split('-')
            main_course_name = line[0].lower()
            courses = line[1].strip().split('/')
            courses = list(map(lambda x: x.lower(), courses))
            get_pre_requisite(df, main_course_name, courses, pre_requisites)
    return pre_requisites


def find_course_info(df, course_name):
    # Create a log for inexistent courses in my registers but not in 'oferta académica' of UCN
    row = df[df['TITULO'] == course_name].values.flatten().tolist()
    if not row:
        log_file = open("logs.txt", "a")
        log_file.write(course_name + "\n")
        log_file.close()
    return row


def get_pre_requisite(df, main_course_name, courses_pre_requisites, pre_requisites_dict):
    # need to search a row who contains course name in their 'TITULO' column
    # after that, cast their row (actually a dataframe with a single row) to a list()
    # row[0] = code-id, row[1] = course name, row[2] = course credits
    row = find_course_info(df, main_course_name)
    main_course_code = row[0]
    for course in courses_pre_requisites:
        find_and_add_relations_dict(df, main_course_code, pre_requisites_dict, course)


def find_and_add_relations_dict(df, main_course_code, pre_requisites_dict, course):
    star_pre_requisites = manage_star_pre_requisites(course)
    if star_pre_requisites:
        for element in star_pre_requisites:
            find_and_add_relations_dict(df, main_course_code, pre_requisites_dict, element)
        return
    else:
        course_code = find_course_info(df, course)[0]
    # I preferred to use 'try', 'except' and 'finally' to avoid repeat same line of code in 'try' and 'except'
    # whatever, it could be handled without 'finally' statement
    try:
        pre_requisites_dict[main_course_code]
    except KeyError:
        pre_requisites_dict[main_course_code] = list()
    finally:
        pre_requisites_dict[main_course_code].append(course_code)


def manage_star_pre_requisites(pre_requisite):
    pre_requisites = list()
    if pre_requisite == '*' or pre_requisite == '**':
        with open('PCA.txt', encoding='utf8') as fr:
            for line in fr:
                pre_requisites.append(line.strip().lower())
    elif pre_requisite == '**':
        pass  # WE NEED CODE HERE!!
    return pre_requisites


if __name__ == '__main__':
    df1 = pd.read_excel('oferta1.xlsx')
    df2 = pd.read_excel('oferta2.xlsx')
    df = extract_transform_load(df1, df2)
    get_buttons(df)
    dct = create_pre_requisites_dict(df)
    dct = {k.upper(): list(map(str.upper, v)) for k, v in dct.items()}
    js_file = open("jsCode.txt", "a")
    js_file.write(dct.__repr__().replace('{', '').replace('}', ''))
    js_file.close()
