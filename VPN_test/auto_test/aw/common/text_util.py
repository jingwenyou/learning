from pathlib import Path

base_dir = Path(__file__).parent.parent.parent
# print(base_dir)


def read_txt(text_file):
    """读取txt文件"""
    with open(text_file, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()


def write_txt(text_file, data):
    """追加写入txt文件"""
    with open(text_file, 'a', encoding='utf-8', errors='ignore') as f:
        f.write(data)


def extract_txt(text_file, data):
    """覆盖写入txt文件"""
    # 覆盖保存
    with open(text_file, 'w+', encoding='utf-8') as f:
        f.write(data)
    # 读取
    # return read_txt(text_file)


def truncate_txt(text_file):
    """清空txt文件"""
    with open(text_file, 'w') as f:
        f.truncate()


def read_txt_handel(text_file='%s/data/run_result.txt' % base_dir):
    """将保存运行结果的txt数据，处理成想要的格式"""
    value = read_txt(text_file=text_file)
    print(value)
    l_reponse = []
    l_ispass = []
    for i in value[0:-1].split("|"):
        l_reponse.append((i.split('__')[0]))
        l_ispass.append(i.split('__')[1])
    # print(l_reponse)
    # print(l_ispass)

    return l_reponse, l_ispass


# if __name__ == '__main__':
#     read_txt_handel()
