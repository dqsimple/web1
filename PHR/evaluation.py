result_path = "data/UH/UH_test_small_result.jsonl"
gt_path = "data/UH/UH_test_small_gt.jsonl"
from nltk.translate.bleu_score import corpus_bleu, sentence_bleu
from pyrouge import Rouge155

result_list = []
gt_list = []
with open(result_path, 'r', encoding='utf-8') as result_file, open(gt_path, 'r', encoding='utf-8') as gt_file:
    for result_line, gt_line in zip(result_file, gt_file):
        result_list.append(result_line.strip())
        gt_list.append([gt_line.strip()])
# 计算 BLEU 分数
bleu_score = corpus_bleu(result_list, gt_list)

# 使用 Rouge
rouge = Rouge155()
rouge.rouge_dir = 'D:/Code/ROUGE-1.5.5'
rouge._home_dir = 'D:/Code/ROUGE-1.5.5'
rouge.system_dir = system_dir
rouge.model_dir = model_dir
rouge.system_filename_pattern = '(\d+)_system.txt'
rouge.model_filename_pattern = '#ID#_model.txt'
score = rouge.convert_and_evaluate()

print(f"BLEU Score: {bleu_score}")
print(score)