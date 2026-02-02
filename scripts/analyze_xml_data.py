#!/usr/bin/env python3
"""分析聊天数据中的 XML 消息类型。"""

import json
import re
from collections import Counter
from pathlib import Path


def main():
    data_file = Path("chat_data/1.json")

    if not data_file.exists():
        print(f"错误: 找不到文件 {data_file}")
        return

    with open(data_file, 'r') as f:
        data = json.load(f)

    messages = data.get('messages', [])

    print("=" * 80)
    print("聊天数据 XML 消息统计分析")
    print("=" * 80)
    print(f"\n总消息数: {len(messages)}\n")

    # 统计消息类型
    print("=" * 80)
    print("1. 消息类型分布")
    print("=" * 80)
    type_counts = Counter(msg.get('localType') for msg in messages)

    print(f"{'类型':<15} {'数量':>10} {'说明'}")
    print("-" * 80)

    type_descriptions = {
        '1': '文本消息',
        '3': '图片消息',
        '47': '表情消息',
        '21474836529': '分享消息（文章/链接）',
        '244813135921': '未知类型',
        '266287972401': '拍一拍',
        '10000': '系统消息',
        '42': '语音消息',
        '43': '视频消息',
    }

    for msg_type, count in type_counts.most_common():
        desc = type_descriptions.get(str(msg_type), '未知')
        print(f"{str(msg_type):<15} {count:>10} {desc}")

    # 统计 XML 消息
    print("\n" + "=" * 80)
    print("2. XML 消息统计")
    print("=" * 80)

    xml_messages = []
    for msg in messages:
        content = msg.get('content', '')
        if content and '<?xml' in content:
            xml_messages.append({
                'type': msg.get('localType'),
                'content': content,
                'sender': msg.get('senderDisplayName', ''),
            })

    print(f"包含 XML 的消息: {len(xml_messages)} 条\n")

    # 统计 appmsg 类型
    print("=" * 80)
    print("3. appmsg 类型分布")
    print("=" * 80)

    appmsg_types = Counter()
    appmsg_samples = {}

    for msg in xml_messages:
        content = msg['content']

        # 提取 type
        type_match = re.search(r'<type>(\d+)</type>', content)
        if type_match:
            appmsg_type = type_match.group(1)
            appmsg_types[appmsg_type] += 1

            # 保存每种类型的示例
            if appmsg_type not in appmsg_samples:
                appmsg_samples[appmsg_type] = []

            if len(appmsg_samples[appmsg_type]) < 2:
                title_match = re.search(r'<title>([^<]+)</title>', content)
                title = title_match.group(1) if title_match else "无标题"
                appmsg_samples[appmsg_type].append({
                    'title': title,
                    'sender': msg['sender'],
                })

    type_names = {
        '5': '文章/链接分享',
        '62': '拍一拍',
        '1': '文本',
        '57': '位置消息',
        '3': '图片',
        '43': '视频',
        '34': '语音',
        '42': '语音',
        '47': '表情',
        '49': '文件',
        '2000': '转账',
        '2001': '红包',
        '2002': '红包',
        '2003': '红包',
    }

    print(f"{'appmsg 类型':<10} {'数量':>8} {'名称':<20} {'示例标题'}")
    print("-" * 80)

    for type_val, count in appmsg_types.most_common():
        type_name = type_names.get(type_val, f'未知类型{type_val}')
        samples = appmsg_samples.get(type_val, [])
        sample_title = samples[0]['title'][:40] if samples else "无"

        print(f"{type_val:<10} {count:>8} {type_name:<20} {sample_title}")

    # 统计标题类型
    print("\n" + "=" * 80)
    print("4. 标题分类统计")
    print("=" * 80)

    title_categories = {
        '拍一拍': 0,
        '文章分享': 0,
        '链接分享': 0,
        '其他': 0,
    }

    link_samples = []

    for msg in xml_messages:
        content = msg['content']
        title_match = re.search(r'<title>([^<]+)</title>', content)

        if title_match:
            title = title_match.group(1)

            if '拍了拍' in title:
                title_categories['拍一拍'] += 1
            elif 'mp.weixin.qq.com' in content or 'http' in content:
                if 'des' in content or '<url>' in content:
                    title_categories['文章分享'] += 1

                    # 保存文章示例
                    if len(link_samples) < 5:
                        url_match = re.search(r'<url>([^<]+)</url>', content)
                        des_match = re.search(r'<des>([^<]+)</des>', content)

                        link_samples.append({
                            'title': title,
                            'url': url_match.group(1) if url_match else '无URL',
                            'des': des_match.group(1) if des_match else '无描述',
                        })
                else:
                    title_categories['链接分享'] += 1
            else:
                title_categories['其他'] += 1

    print(f"{'分类':<15} {'数量':>10}")
    print("-" * 80)
    for category, count in title_categories.items():
        print(f"{category:<15} {count:>10}")

    # URL 统计
    print("\n" + "=" * 80)
    print("5. URL 链接统计")
    print("=" * 80)

    has_url = sum(1 for msg in xml_messages if '<url>' in msg['content'])
    has_des = sum(1 for msg in xml_messages if '<des>' in msg['content'])

    print(f"包含 <url> 标签的消息: {has_url} 条")
    print(f"包含 <des> 标签的消息: {has_des} 条")

    if link_samples:
        print(f"\n文章分享示例 ({len(link_samples)} 个):")
        print("-" * 80)
        for i, sample in enumerate(link_samples, 1):
            print(f"\n{i}. 标题: {sample['title']}")
            print(f"   URL: {sample['url'][:80]}")
            print(f"   描述: {sample['des'][:80]}")

    # 字段统计
    print("\n" + "=" * 80)
    print("6. 字段使用情况")
    print("=" * 80)

    fields = ['content', 'parsedContent', 'rawContent', 'source', 'xml_content']
    print(f"{'字段名':<20} {'包含该字段的消息数':>20}")
    print("-" * 80)

    for field in fields:
        if field == 'xml_content':
            # xml_content 是我们处理后的字段，不会在原始数据中
            count = 0
        else:
            count = sum(1 for msg in messages if msg.get(field))
        print(f"{field:<20} {count:>20}")

    # 总结
    print("\n" + "=" * 80)
    print("总结")
    print("=" * 80)

    link_share_count = title_categories['文章分享']
    pai_pai_count = title_categories['拍一拍']

    print(f"• 可解析为链接卡片的消息: {link_share_count} 条")
    print(f"• 拍一拍消息: {pai_pai_count} 条")
    print(f"• 其他 XML 消息: {len(xml_messages) - link_share_count - pai_pai_count} 条")

    print("\n建议:")
    if link_share_count > 0:
        print(f"✓ 数据中有 {link_share_count} 条文章分享消息可以渲染为链接卡片")
    else:
        print("✗ 当前数据中没有文章分享消息（拍一拍不算）")

    if pai_pai_count > 0:
        print(f"  有 {pai_pai_count} 条拍一拍消息，只包含标题，没有 URL")


if __name__ == "__main__":
    main()
