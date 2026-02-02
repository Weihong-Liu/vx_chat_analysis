import xml.etree.ElementTree as ET
from typing import Dict, List

def normalize_xml(xml_text: str) -> str:
    """
    清洗微信 XML：
    - 去 BOM
    - 去首部多余空白
    - 裁剪到 <?xml 开始
    - 去末尾多余引号
    """
    xml_text = xml_text.strip()

    # 去 BOM
    if xml_text.startswith("\ufeff"):
        xml_text = xml_text.lstrip("\ufeff")

    # 确保从 <?xml 开始
    xml_pos = xml_text.find("<?xml")
    if xml_pos != -1:
        xml_text = xml_text[xml_pos:]

    # 有些导出会多一个 "
    if xml_text.endswith('"'):
        xml_text = xml_text[:-1]

    return xml_text

def parse_wechat_record(xml_text: str) -> Dict:
    """
    解析微信 type=19 聊天记录 XML
    """
    root = ET.fromstring(xml_text)

    appmsg = root.find("appmsg")
    if appmsg is None or appmsg.find("type").text != "19":
        raise ValueError("不是聊天记录卡片（type=19）")

    title = appmsg.findtext("title", "")

    recorditem = appmsg.find("recorditem")
    record_xml = recorditem.text.strip()

    record_root = ET.fromstring(record_xml)
    recordinfo = record_root.find("recordinfo")
    datalist = recordinfo.find("datalist")

    messages = []

    for item in datalist.findall("dataitem"):
        datatype = item.attrib.get("datatype")
        msg = {
            "sender": item.findtext("sourcename"),
            "time": item.findtext("sourcetime"),
            "datatype": datatype,
        }

        # ---------- 文本 ----------
        if datatype == "1":
            msg.update({
                "type": "text",
                "text": item.findtext("datadesc", "")
            })

        # ---------- 图片 ----------
        elif datatype == "2":
            msg.update({
                "type": "image",
                "format": item.findtext("datafmt"),
                "size": item.findtext("datasize"),
                "cdn_url": item.findtext("cdndataurl"),
                "cdn_key": item.findtext("cdndatakey"),
            })

        # ---------- 链接 / 公众号 / GitHub ----------
        elif datatype == "5":
            msg.update({
                "type": "link",
                "title": item.findtext("datatitle"),
                "desc": item.findtext("datadesc"),
                "url": item.findtext("streamweburl"),
            })

        # ---------- 视频号 Finder ----------
        elif datatype == "22":
            finder = item.find("finderFeed")
            if finder is not None:
                media = finder.find(".//media")
                msg.update({
                    "type": "finder_video",
                    "author": finder.findtext("nickname"),
                    "desc": finder.findtext("desc"),
                    "duration": media.findtext("videoPlayDuration") if media is not None else None,
                    "video_url": media.findtext("url") if media is not None else None,
                })

        else:
            msg.update({
                "type": "unknown",
                "raw": ET.tostring(item, encoding="unicode")
            })

        messages.append(msg)

    return {
        "title": title,
        "count": len(messages),
        "messages": messages
    }


if __name__ == "__main__":
    xml_text = "\n<?xml version=\"1.0\"?>\n<msg>\n\t<appmsg appid=\"\" sdkver=\"0\">\n\t\t<title>bald0wang的聊天记录</title>\n\t\t<des>bald0wang: [链接] GitHub - HKUDS/DeepTutor: \"DeepTutor: AI-Powered Personalized Learning Assistant\"\nbald0wang: [图片]\nbald0wang: [嘿哈]这个学习智能体框架在这\nbald0wang: 还有配合</des>\n\t\t<action />\n\t\t<type>19</type>\n\t\t<showtype>0</showtype>\n\t\t<soundtype>0</soundtype>\n\t\t<mediatagname />\n\t\t<messageext />\n\t\t<messageaction />\n\t\t<content />\n\t\t<contentattr>0</contentattr>\n\t\t<url />\n\t\t<lowurl />\n\t\t<dataurl />\n\t\t<lowdataurl />\n\t\t<songalbumurl />\n\t\t<songlyric />\n\t\t<template_id />\n\t\t<appattach>\n\t\t\t<totallen>0</totallen>\n\t\t\t<attachid />\n\t\t\t<emoticonmd5></emoticonmd5>\n\t\t\t<fileext />\n\t\t\t<aeskey></aeskey>\n\t\t</appattach>\n\t\t<extinfo />\n\t\t<sourceusername />\n\t\t<sourcedisplayname />\n\t\t<thumburl />\n\t\t<md5 />\n\t\t<statextstr />\n\t\t<recorditem><![CDATA[<recordinfo><fromscene>0</fromscene><favcreatetime>0</favcreatetime><isChatRoom>0</isChatRoom><title>bald0wang的聊天记录</title><desc>bald0wang: [链接] GitHub - HKUDS/DeepTutor: \"DeepTutor: AI-Powered Personalized Learning Assistant\"\nbald0wang: [图片]\nbald0wang: [嘿哈]这个学习智能体框架在这\nbald0wang: 还有配合</desc><datalist count=\"10\"><dataitem datatype=\"5\" dataid=\"755a413916a184a3f493fc57409def1c\"><sourcename>bald0wang</sourcename><sourceheadurl>https://wx.qlogo.cn/mmhead/ver_1/HjibtLHBFjYo3VYic4iaE8CNZ8ngMAoreFCicapvXBFe6oRxBjHiak7ibzWbR39KTcjvaW8gVXmC4ibibRJMPG2WWIsPQB06mcZCZ0VsTgibwIYAfTsk/96</sourceheadurl><sourcetime>2026-01-08 12:41:45</sourcetime><datatitle>GitHub - HKUDS/DeepTutor: \"DeepTutor: AI-Powered Personalized Learning Assistant\"</datatitle><datadesc>\"DeepTutor: AI-Powered Personalized Learning Assistant\" - HKUDS/DeepTutor</datadesc><thumbsize>54564</thumbsize><thumbfiletype>1</thumbfiletype><cdnthumburl>3057020100044b304902010002048cfcb47402032dcb0d020428c16724020469606195042438616235313835382d306534652d343437622d623531622d3365303931393436323833320204059420010201000405004c4e6100</cdnthumburl><cdnthumbkey>0b089f38d76ea5f5eff10ed7f28e674b</cdnthumbkey><thumbfullmd5>420861fe695d86d8cd3209db9a7081c9</thumbfullmd5><streamweburl>https://github.com/HKUDS/DeepTutor</streamweburl><srcMsgCreateTime>1767847305</srcMsgCreateTime><messageuuid>e3f42bd91e4ae7ae03c27b7b50fb5316_</messageuuid><fromnewmsgid>1942600359503004299</fromnewmsgid><dataitemsource><hashusername>034a9e74a0a8d260ed4487bdd07846b89ef7f472956e37d2e26066518fa1c7ca</hashusername></dataitemsource><weburlitem><title>GitHub - HKUDS/DeepTutor: \"DeepTutor: AI-Powered Personalized Learning Assistant\"</title><desc>\"DeepTutor: AI-Powered Personalized Learning Assistant\" - HKUDS/DeepTutor</desc></weburlitem></dataitem><dataitem datatype=\"2\" dataid=\"ac4cf24b4bd4aedc13bb66b301d9229a\"><datafmt>jpg</datafmt><sourcename>bald0wang</sourcename><sourceheadurl>https://wx.qlogo.cn/mmhead/ver_1/HjibtLHBFjYo3VYic4iaE8CNZ8ngMAoreFCicapvXBFe6oRxBjHiak7ibzWbR39KTcjvaW8gVXmC4ibibRJMPG2WWIsPQB06mcZCZ0VsTgibwIYAfTsk/96</sourceheadurl><sourcetime>2026-01-08 12:46:53</sourcetime><datadesc>[图片]</datadesc><thumbsize>3495</thumbsize><cdndataurl>3057020100044b304902010002048cfcb47402032dcb0d020464c167240204696061d8042461316438656237302d616465372d346638642d396334342d3430643539613139373237620204059820010201000405004c56f900</cdndataurl><cdndatakey>7c96ee1959d862bf050682323a29722a</cdndatakey><filetype>1</filetype><thumbfiletype>1</thumbfiletype><cdnthumburl>3057020100044b304902010002048cfcb47402032dcb0d020428c16724020469606196042434653136313564382d623062302d343663352d626634302d3030373365646361303539300204059420010201000405004c4e6100</cdnthumburl><cdnthumbkey>cea74f7323facb6ffdff6a141b3d23ce</cdnthumbkey><fullmd5>fefe35c541cf6e56c62d8c705d261a23</fullmd5><thumbfullmd5>fd5a619a183d9bc879d99cf57f549a80</thumbfullmd5><datasize>5710582</datasize><srcMsgCreateTime>1767847613</srcMsgCreateTime><messageuuid>0d99656d222102930fb5737002ae717d_</messageuuid><fromnewmsgid>6770498085013545696</fromnewmsgid><dataitemsource><hashusername>034a9e74a0a8d260ed4487bdd07846b89ef7f472956e37d2e26066518fa1c7ca</hashusername></dataitemsource></dataitem><dataitem datatype=\"1\" dataid=\"8262efedcaa74a9c2e3ed4c9d17c0a04\"><sourcename>bald0wang</sourcename><sourceheadurl>https://wx.qlogo.cn/mmhead/ver_1/HjibtLHBFjYo3VYic4iaE8CNZ8ngMAoreFCicapvXBFe6oRxBjHiak7ibzWbR39KTcjvaW8gVXmC4ibibRJMPG2WWIsPQB06mcZCZ0VsTgibwIYAfTsk/96</sourceheadurl><sourcetime>2026-01-08 12:47:23</sourcetime><datadesc>[嘿哈]这个学习智能体框架在这</datadesc><srcMsgCreateTime>1767847643</srcMsgCreateTime><fromnewmsgid>5359712325337144379</fromnewmsgid><dataitemsource><hashusername>034a9e74a0a8d260ed4487bdd07846b89ef7f472956e37d2e26066518fa1c7ca</hashusername></dataitemsource></dataitem><dataitem datatype=\"1\" dataid=\"08e1930b25047d15e404a7a72bb4e163\"><sourcename>bald0wang</sourcename><sourceheadurl>https://wx.qlogo.cn/mmhead/ver_1/HjibtLHBFjYo3VYic4iaE8CNZ8ngMAoreFCicapvXBFe6oRxBjHiak7ibzWbR39KTcjvaW8gVXmC4ibibRJMPG2WWIsPQB06mcZCZ0VsTgibwIYAfTsk/96</sourceheadurl><sourcetime>2026-01-08 12:48:02</sourcetime><datadesc>还有配合鼎伦发的提示词那一篇</datadesc><srcMsgCreateTime>1767847682</srcMsgCreateTime><fromnewmsgid>8071478384839599751</fromnewmsgid><dataitemsource><hashusername>034a9e74a0a8d260ed4487bdd07846b89ef7f472956e37d2e26066518fa1c7ca</hashusername></dataitemsource></dataitem><dataitem datatype=\"5\" dataid=\"e1eb1503d7c307359b285954d362fb33\"><brandid>gh_94dba26f8ca0</brandid><sourcename>bald0wang</sourcename><sourceheadurl>https://wx.qlogo.cn/mmhead/ver_1/HjibtLHBFjYo3VYic4iaE8CNZ8ngMAoreFCicapvXBFe6oRxBjHiak7ibzWbR39KTcjvaW8gVXmC4ibibRJMPG2WWIsPQB06mcZCZ0VsTgibwIYAfTsk/96</sourceheadurl><sourcetime>2026-01-08 12:48:51</sourcetime><datatitle>分享6个平时我最常用的Prompt心法。</datatitle><datadesc>做你自己问题的导演。</datadesc><thumbsize>32444</thumbsize><thumbfiletype>1</thumbfiletype><cdnthumburl>3057020100044b304902010002048cfcb47402032dcb0d020428c16724020469606196042437396635363063352d616139612d343138392d623035632d3233336238653863356662380204059820010201000405004c4ff100</cdnthumburl><cdnthumbkey>895636a7b3f66136d9e6dcd09dcf802c</cdnthumbkey><thumbfullmd5>42b933b6111953aa3de269a8bf862cd5</thumbfullmd5><streamweburl>https://mp.weixin.qq.com/s?__biz=MzIyMzA5NjEyMA==&amp;mid=2647678476&amp;idx=1&amp;sn=1e7c408367fec1e41b8f882d182e05f2&amp;chksm=f1af8b9e563ede8c26b737175878ba0020aebe45732c09ca23062c199a7a169996c08ea4bd59&amp;mpshare=1&amp;scene=1&amp;srcid=0108uzNtOEe5qVboFn8GEiaF&amp;sharer_shareinfo=e98226e1491320ea3a4bde8141d81ec4&amp;sharer_shareinfo_first=e98226e1491320ea3a4bde8141d81ec4#rd</streamweburl><srcMsgCreateTime>1767847731</srcMsgCreateTime><messageuuid>b82532fe7b5efda59d5325de7533ae1d_</messageuuid><fromnewmsgid>2646414583744377868</fromnewmsgid><dataitemsource><hashusername>034a9e74a0a8d260ed4487bdd07846b89ef7f472956e37d2e26066518fa1c7ca</hashusername></dataitemsource><weburlitem><title>分享6个平时我最常用的Prompt心法。</title><desc>做你自己问题的导演。</desc></weburlitem></dataitem><dataitem datatype=\"1\" dataid=\"eaecd66ae7169951d38455e177170eb8\"><sourcename>白客</sourcename><sourceheadurl>https://wx.qlogo.cn/mmhead/ver_1/L1kfkVJqgcMRX1xVFiaw1bUM8fTd3dSPkv8QVFib0sMicicHbbOKne5xI3gPDa6wFkiaB6k6TXQOGvgvnUK23g5SConDZpPibKZ7zgtgZYIYyHiams/96</sourceheadurl><sourcetime>2026-01-08 12:49:22</sourcetime><datadesc>这个确实好用我觉得</datadesc><srcMsgCreateTime>1767847762</srcMsgCreateTime><messageuuid>b82532fe7b5efda59d5325de7533ae1d_</messageuuid><fromnewmsgid>5896935529659346912</fromnewmsgid><dataitemsource><hashusername>77a6abd0afa630c23585f685f2ea82f368da4c3e4bb291d794d286f0792cb5cf</hashusername></dataitemsource></dataitem><dataitem datatype=\"1\" dataid=\"02a5c68c8f8b00584a67b2b8d7d45c4f\"><sourcename>我爱吃饭</sourcename><sourceheadurl>https://wx.qlogo.cn/mmhead/ver_1/uX5My9Nen7fVur9icFTwcjkicia6kLPEBAZfIDoColiceqhic11VwdWr2yIx3ZZ4JicROib61VbAIFrhicI0sNO7SsEtzrRpepXg5xWd7udAdC0O6BnwgIib7qHtTpUjL8Uic3Lksty0VUpn9lExQyk7WwFjq2ZQ/96</sourceheadurl><sourcetime>2026-01-08 12:50:03</sourcetime><datadesc>每天晚上睡前都能准时刷到晓辉博士</datadesc><srcMsgCreateTime>1767847803</srcMsgCreateTime><fromnewmsgid>6724227985679423357</fromnewmsgid><dataitemsource><hashusername>f7f7634739f1259c950118cbdef3d90360435c6dcefaad001e24a7aa0bf13f62</hashusername></dataitemsource></dataitem><dataitem datatype=\"1\" dataid=\"6fb9e5792e2b60e4db0d0a17dafacb98\"><sourcename>我爱吃饭</sourcename><sourceheadurl>https://wx.qlogo.cn/mmhead/ver_1/uX5My9Nen7fVur9icFTwcjkicia6kLPEBAZfIDoColiceqhic11VwdWr2yIx3ZZ4JicROib61VbAIFrhicI0sNO7SsEtzrRpepXg5xWd7udAdC0O6BnwgIib7qHtTpUjL8Uic3Lksty0VUpn9lExQyk7WwFjq2ZQ/96</sourceheadurl><sourcetime>2026-01-08 12:50:07</sourcetime><datadesc>看完美美睡觉</datadesc><srcMsgCreateTime>1767847807</srcMsgCreateTime><fromnewmsgid>1808399473273193250</fromnewmsgid><dataitemsource><hashusername>f7f7634739f1259c950118cbdef3d90360435c6dcefaad001e24a7aa0bf13f62</hashusername></dataitemsource></dataitem><dataitem datatype=\"22\" dataid=\"8634669118d6c06c105b8ed2451fe778\"><sourcename>bald0wang</sourcename><sourceheadurl>https://wx.qlogo.cn/mmhead/ver_1/HjibtLHBFjYo3VYic4iaE8CNZ8ngMAoreFCicapvXBFe6oRxBjHiak7ibzWbR39KTcjvaW8gVXmC4ibibRJMPG2WWIsPQB06mcZCZ0VsTgibwIYAfTsk/96</sourceheadurl><sourcetime>2026-01-08 12:50:33</sourcetime><datatitle>晓辉博士的视频</datatitle><datadesc>苏格拉底提问法，真的是一个让AI帮你理清一些模糊想法和纠结的很好的办法，关键是在AI从一个无所不知的回答者转换为提问者之后，我们人类脑海中那些独特的想法和闪光的直觉有了出口。当所有的对话都围绕着我们自己的想法展开时，我们就能更清楚地认识自己，也能更好地激发大脑的潜力。</datadesc><srcMsgCreateTime>1767847833</srcMsgCreateTime><messageuuid>dd4b493691654e474c17dc23b454433e_</messageuuid><fromnewmsgid>5393800306544305383</fromnewmsgid><dataitemsource><hashusername>034a9e74a0a8d260ed4487bdd07846b89ef7f472956e37d2e26066518fa1c7ca</hashusername></dataitemsource><finderFeed><objectId>14800385500806515371</objectId><feedType>4</feedType><nickname>晓辉博士</nickname><avatar>https://wx.qlogo.cn/finderhead/ver_1/qnNJib9eU8DlZiahXOAEnqF1iaBmR0NpWxurUIP4NhSvfbphHZYjJmoUnar8epyczOvDvowThqwt88uiatZqiaGcyPqxYs1mtQ9LsSNic9f0hcdx67RoKO8I6y4ljjM0F923l0ibrHzbtHr1S3ZibqGGxLEjvw/0</avatar><desc>苏格拉底提问法，真的是一个让AI帮你理清一些模糊想法和纠结的很好的办法，关键是在AI从一个无所不知的回答者转换为提问者之后，我们人类脑海中那些独特的想法和闪光的直觉有了出口。当所有的对话都围绕着我们自己的想法展开时，我们就能更清楚地认识自己，也能更好地激发大脑的潜力。</desc><mediaCount>1</mediaCount><username>v2_060000231003b20faec8c7e78f18c6d7c800ec30b077d6a4002b59c37fddf6a5e548d770f57a@finder</username><mediaList><media><mediaType>4</mediaType><url>http://wxapp.tc.qq.com/251/20302/stodownload?encfilekey=Cvvj5Ix3eez3Y79SxtvVL0L7CkPM6dFibusn4vVFEyiaoGT9vlmKajhh0689uAcARZcIyPJ1nOqhIdDKibcnicbPne3q1LaO6k9hPSboM9oMBTuApSW0IKjibrN3A2y0tuDKy7g2iapf2rQUhs3ibgjb8Xvhg&amp;hy=SZ&amp;idx=1&amp;m=0102a534b080499a9722322e7f1a3764&amp;uzid=7a1ca&amp;token=6xykWLEnztLpQZdgbYPmicvA5IFWdhuvicOyoAafmhjShszHc5KZeyHCdzpVxJbg1BwVZakEqUw2ibzIXSMAlop2zdAVKeux2uyeJENAkQv0TbmWyQJAxXJnFiafptrY8aYNIIia5VmTicfjsUGX5RManUn0VB7W6kIDPktSOTpiarBm6c&amp;basedata=CAESBnhXVDEyMRoGeFdUMTExGgZ4V1QxMTIaBnhXVDEyNhoGeFdUMTEzGgZ4V1QxMjcaBnhXVDEyMRoGeFdUMTI4IgwKCgoGeFdUMTEyEAEqBwiYHRAAGAI&amp;sign=-EX3xlrfL9j3BWyAkbjMO-ezTf94d2qxmrj6FSpaUEoa4HVsN0Nwr1Sod-DoY8kxfIrBaCOu64wnvNWbE_COFA&amp;extg=10ec300&amp;svrbypass=AAuL%2FQsFAAABAAAAAADVh8IqoU%2Fo6K11hzdfaRAAAADnaHZTnGbFfAj9RgZXfw6VYtjeqpRakhCk47GahFw1cqtG8Ud5vLY0vEpcvXUvT8vLCnJPBRE503c%3D&amp;svrnonce=1767847815</url><thumbUrl>http://wxapp.tc.qq.com/251/20304/stodownload?encfilekey=oibeqyX228riaCwo9STVsGLIBn9G5YG8Znte36DiarE2qcFE1icZFUy7oHoBJWAdTGNlR5RlB4EPytF1XaI6sHJtogFocaTjhbgcibNicttYE1pIDHtOVptl8nib9pp325mFvKlA3VwKuY6BNE&amp;hy=SZ&amp;idx=1&amp;m=d5ae02506de0c5f68945689a2d850fac&amp;uzid=1&amp;picformat=200&amp;wxampicformat=503&amp;token=6xykWLEnztKIzBicPuvgFxmZGY5vNRzwm3SUYWcwI7W8hMW9iaoeThXpG8cJPBicPhUyZAPSrqaX91ibO6Aaoj5IaUSWjqINfpQ4rAeYJsNrf0MXvNsGStwt1PEQVO6hS4lneqdsqial94BtW1uyPYk3K4n8QLUgiaUQaG</thumbUrl><width>1080.0</width><height>1920.0</height><videoPlayDuration>401</videoPlayDuration></media></mediaList></finderFeed></dataitem><dataitem datatype=\"1\" dataid=\"f2de1142ff56812b4b232c0616922416\"><sourcename>bald0wang</sourcename><sourceheadurl>https://wx.qlogo.cn/mmhead/ver_1/HjibtLHBFjYo3VYic4iaE8CNZ8ngMAoreFCicapvXBFe6oRxBjHiak7ibzWbR39KTcjvaW8gVXmC4ibibRJMPG2WWIsPQB06mcZCZ0VsTgibwIYAfTsk/96</sourceheadurl><sourcetime>2026-01-08 12:51:14</sourcetime><datadesc>健脑房搞起来~</datadesc><srcMsgCreateTime>1767847874</srcMsgCreateTime><fromnewmsgid>1463979925884415100</fromnewmsgid><dataitemsource><hashusername>034a9e74a0a8d260ed4487bdd07846b89ef7f472956e37d2e26066518fa1c7ca</hashusername></dataitemsource></dataitem></datalist></recordinfo>]]></recorditem>\n\t</appmsg>\n\t<extcommoninfo>\n\t\t<media_expire_at>1769133785</media_expire_at>\n\t</extcommoninfo>\n\t<fromusername>wxid_fdcm0ng0ydzq22</fromusername>\n\t<scene>0</scene>\n\t<appinfo>\n\t\t<version>1</version>\n\t\t<appname />\n\t</appinfo>\n\t<commenturl />\n</msg>\n"

    data = parse_wechat_record(normalize_xml(xml_text))

    import json
    print(json.dumps(data, ensure_ascii=False, indent=2))