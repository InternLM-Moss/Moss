from similarities import BertSimilarity

from loguru import logger
import re

class NLP_Similar:
    def __init__(self,model_name_or_path):
        self.nlp_model = BertSimilarity(model_name_or_path=model_name_or_path)
        self.cn_regx = re.compile("[^\u4e00-\u9fa5^a-z^A-Z^0-9]") 

    def str_regx(self, content):
        """
        去除非汉字、字母、数字类符号，减少干扰
        """
        content = self.cn_regx.sub('', content)
        return content
    
    def search(self, query, jobtask_data, score=0.85, topN=1):
        #将查询语句，去除符号字符
        query = self.str_regx(query)

        corpus = []
        corpus_dict = {}
        for i in jobtask_data['data']['rows']:
            for n in i['job_nlu']:
                nlu_item = self.str_regx(n['job_nlu_item'])
                corpus.append(nlu_item)
                corpus_dict[nlu_item] = i


        self.nlp_model.add_corpus(corpus)
        ret = self.nlp_model.search(query, topn=topN)
        result = {}
        logger.info(f'ret: {ret[0]}')
        for key, value in ret[0].items():
            if value > score:
                idx = key
                result = corpus_dict[corpus[idx]]

        logger.info(f"NLP_Similar search return result: {result}")
        return result

if __name__ == '__main__':
    nlp = NLP_Similar('/data/text2vec-base-chinese')
    jobtask_data  =  {'status': 0, 'msg': 'success', 'data': {'count': 0, 'rows': [{'id': 1, 'update_time': '2024-03-19 00:51:09', 'job_name': '你是谁', 'job_nlu': [{'job_nlu_item': '你是谁'}, {'job_nlu_item': '>你叫什么'}, {'job_nlu_item': '你是'}], 'job_nlu_web': [{'item': '你是谁'}, {'item': '你叫什么'}, {'item': '你是'}], 'slot_json': [], 'api_type': 'txt_msg', 'web_msg': '你好，我是Moss，很高兴认识你。有什么我可以帮助你的吗？', 'txt_msg': '你好，我是Moss，很高兴认识你。有什么我可以帮助你的吗？', 'api': '', 'llm': '0', 'comment': ''}], 'total': 1}}
    nlp.search('你是', jobtask_data)