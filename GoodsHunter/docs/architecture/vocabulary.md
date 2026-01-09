## 这里是专有名词的列表，为了确保数据处理的准确性，请在后续对话中严格遵守以下专有名词的定义，不得混淆：

词表：
site:抓取网站的站点域名，譬如wwww.watchnian.com
item_id：指被抓取的商品，在原网站的唯一标识符（字符串）
source_id:指被抓取的商品，全局的唯一标识符，site:category:item_id
id：crawler_item表的id字段，指目前用来检索的商品id
product表id：代表归一化的商品id，理论上 category:brand_name:model_name:model_no代表了归一化的商品。
category：类型，比如手表，珠宝，箱包，等等