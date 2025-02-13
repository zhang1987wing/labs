import csv


def save_links_to_csv(links, filename):
    # 写入 collected_links 到 CSV 文件，并添加 'is_used' 字段
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # 写入标题行
        writer.writerow(['post_url', 'is_used'])

        # 写入每个链接和默认 'is_used' 为 False
        for link in links:
            writer.writerow([link, 'False'])


def get_updated_rows_from_csv(filename):
    updated_rows = []  # 用来存储更新后的 CSV 数据

    # 读取 CSV 文件
    with open(filename, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        headers = next(reader)  # 跳过标题行
        updated_rows.append(headers)  # 保存标题行

        # 遍历每一行数据
        for row in reader:
            updated_rows.append(row)

    return updated_rows


def update_csv(filename, updated_rows):
    # 将更新后的数据写回 CSV 文件
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows(updated_rows)
