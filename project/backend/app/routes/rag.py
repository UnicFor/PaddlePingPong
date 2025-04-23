import os
from pathlib import Path
import time
from flask import Blueprint, jsonify, request, g
from dotenv import load_dotenv
import openai
import torch
from ..utils.security import jwt_required
from ..utils.models import User, UserVideo
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from langchain_openai import OpenAIEmbeddings
from langchain.docstore.document import Document
from openai import OpenAI
from ..utils.rag.graphrag import (
    build_retrieval_pipeline,
    build_vector_store,
    process_uploaded_files,
    retrieve_from_graph,
    split_documents,
)
from ..utils.rag.load_and_search_from_datasets import (
    load_dataset_embedding,
    search_from_index,
)
from ..utils.rag.load_data import load_skeleton_keypoint
from ..config import BaseConfig

device = "cuda" if torch.cuda.is_available() else "cpu"

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
qianfan_api_key = os.getenv("QIANFAN_API_KEY")
QIANFAN_MODEL_MAPPING = {
    "ernie-x1": "ernie-x1-32k-preview",
    "ernie-4.5": "ernie-4.5-8k-preview",
    "deepseek-r1": "deepseek-r1",
    "deepseek-v3": "deepseek-v3-241226",
}
rag_bp = Blueprint("api", __name__)

INDEX_FILE = "./app/data/faiss_index"

retrieval_pipeline = None
_INDEX_CACHE = None
_LINES_CACHE = None

_report_paths = []
_N = 0

@rag_bp.route("/upload_eval", methods=["POST"])
def upload_files():
    global retrieval_pipeline
    if "files" not in request.files:
        return (
            jsonify({"status": "error", "error": "No files provided"}),
            400,
        )  # 添加 status 字段

    files = request.files.getlist("files")
    try:
        documents = process_uploaded_files(files)
        texts = split_documents(documents)
        embeddings = OpenAIEmbeddings()
        vector_store = build_vector_store(texts, embeddings)
        retrieval_pipeline = build_retrieval_pipeline(texts, vector_store)
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

    kg = retrieval_pipeline["knowledge_graph"]
    return jsonify(
        {
            "status": "success",
            "message": "Files processed and embeddings generated successfully!",
            "total_nodes": len(kg.nodes),
            "total_edges": len(kg.edges),
        }
    )


@rag_bp.route("/chat", methods=["POST"])
def chat():
    global retrieval_pipeline
    data = request.get_json()
    prompt = data.get("prompt", "")
    chat_history = data.get("chat_history", "")
    mode = data.get("mode", "custom")
    report = data.get("report", "")
    graphrag = data.get("graphrag", False)
    selected_api = data.get("selected_api", "openai")
    selected_model = data.get("selected_model", "gpt-3.5-turbo")

    if mode == "custom":

        if retrieval_pipeline is not None:
            # BM25检索
            ensemble = retrieval_pipeline["ensemble"]
            retrieved_docs = ensemble.invoke(prompt)
            if graphrag:
                # 图检索
                graph_results = retrieve_from_graph(
                    prompt, retrieval_pipeline["knowledge_graph"]
                )
                graph_docs = (
                    [Document(page_content=node) for node in graph_results]
                    if graph_results
                    else []
                )
                docs = graph_docs + retrieved_docs if graph_docs else retrieved_docs

                context = "\n".join([doc.page_content for doc in docs])
                
            else:
                context = "\n".join(
                    f"[Source {i+1}]: {doc.page_content}"
                    for i, doc in enumerate(retrieved_docs)
                )
        else:
            context = " "
    else:
        docs = search_from_index(prompt, k=5)
        context = "\n".join(
            f"[Source {i+1}]: {doc}" for i, doc in enumerate(docs)
        )
    system_prompt = f"""你是一名专业的乒乓球教练和运动动作分析专家。

请根据下方提供的上下文信息，对用户的输入进行分析，并用**纯文本格式**撰写你的回答。你的回答应由结构清晰的段落组成，每个段落之间用两个换行符（\\n\\n）分隔。

不要使用 Markdown、项目符号或编号列表。请使用完整的语句和自然的语言过渡，使你的回答像一篇规范的运动分析报告，便于前端美观展示。

=== 对话历史 ===
{chat_history}

=== 用户此前的分析报告 ===
{report}

=== 上下文信息 ===
{context}

=== 任务 ===
请根据用户的骨骼点数据、击球轨迹和相关背景信息，对其乒乓球动作表现进行结构化分析。你的回答应包含以下四个部分，每部分为一个段落，段落之间使用两个换行符（\\n\\n）分隔：

1. 技术分析：分析用户的击球动作技术，包括优势和不足。
2. 姿态与动作：评估用户的身体姿势、握拍方式、挥拍动作，并提出改进建议。
3. 伤病预防：识别可能存在的运动风险，并提供预防常见运动损伤的建议。
4. 提升建议：推荐适合该用户的训练方式、动作练习或提升方法。

请确保每个部分都使用自然语言进行撰写，段落清晰，逻辑通顺，整体内容完整专业。
=== 注意事项 ===
1、当没有报告输入时，正常回答用户问题，不需要提醒用户输入报告，忽略上面的“=== 用户此前的分析报告 ===”部分。

用户输入：
{prompt}

输出（请使用纯文本格式，段落之间）：
"""



    def generate_openai():
        try:
            chat = ChatOpenAI(
                model_name=selected_model, openai_api_key=openai_api_key, streaming=True
            )
            response_generator = chat.invoke([HumanMessage(content=system_prompt)])

            return response_generator.content
        except Exception as e:
            return f"Error: {str(e)}"

    def generate_qianfan():
        try:
            client = OpenAI(
                api_key=qianfan_api_key,
                base_url="https://qianfan.baidubce.com/v2",
            )
            model = QIANFAN_MODEL_MAPPING.get(selected_model, selected_model)
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "你是乒乓球运动动作分析专家"},
                    {"role": "user", "content": system_prompt},
                ],
                stream=False,
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"\nError: {str(e)}"

    if selected_api.lower() == "openai":
        generator = generate_openai()
    elif selected_api.lower() in ["百度千帆", "qianfan"]:
        generator = generate_qianfan()
    else:

        def error_gen():
            return "不支持的 API 运营商。"

        generator = error_gen()

    return jsonify({"content": generator})


@rag_bp.route("/load_dataset_embedding", methods=["POST"])
def load_dataset_embedding_route():
    global _INDEX_CACHE, _LINES_CACHE
    try:
        index_file = "./app/data/expert_index.index"
        text_file = "./app/data/expert_texts.txt"
        _INDEX_CACHE, _LINES_CACHE = load_dataset_embedding(
            index_file=index_file, text_file=text_file
        )
        index_count = _INDEX_CACHE.ntotal if hasattr(_INDEX_CACHE, "ntotal") else 0
        lines_count = len(_LINES_CACHE) if _LINES_CACHE is not None else 0

        return jsonify({
            "status": "success",
            "message": "Dataset embedding loaded successfully!",
            "index_cache_length": index_count,
            "lines_cache_length": lines_count,
        })
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@rag_bp.route("/load_report", methods=["POST"])
@jwt_required
def load_report():
    req_data = request.get_json()
    video_id = req_data.get("video_id")

    if not video_id:
        return jsonify({"status": "error", "message": "缺少 video_id 参数"}), 400

    # 获取当前用户
    current_user = g.current_user
    user = User.query.get(current_user.user_id)
    if not user:
        return jsonify({"status": "error", "message": "用户不存在"}), 404

    # 验证视频归属
    video = UserVideo.query.filter_by(
        video_id=video_id,
        user_id=user.user_id
    ).first()
    if not video:
        return jsonify({"status": "error", "message": "无权访问该视频"}), 403

    # 构建报告文件路径
    pose_user_dir = Path(BaseConfig.POSE_FOLDER) / f"user_{user.user_id}"
    report_path = pose_user_dir / f"results_{video_id}.md"

    if not report_path.exists():
        return jsonify({"status": "error", "error": "报告文件不存在"}), 404

    try:
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
        return jsonify({"status": "success", "report": content})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@rag_bp.route("/generate_report", methods=["POST"])
@jwt_required
def generate_report():
    req_data = request.get_json()
    video_id = req_data.get("video_id")

    if not video_id:
        return jsonify({"status": "error", "message": "缺少 video_id 参数"}), 400

    # 获取当前用户
    current_user = g.current_user
    user = User.query.get(current_user.user_id)
    if not user:
        return jsonify({"status": "error", "message": "用户不存在"}), 404

    # 验证视频归属
    video = UserVideo.query.filter_by(
        video_id=video_id,
        user_id=user.user_id
    ).first()
    if not video:
        return jsonify({"status": "error", "message": "无权访问该视频"}), 403

    # 构建文件路径（根据video_id）
    pose_video_path = str(Path(BaseConfig.POSE_FOLDER) / f"user_{user.user_id}")
    file_path = Path(pose_video_path) / f"results_{video_id}.json"

    if not os.path.exists(file_path):
        return jsonify({"status": "error", "error": "File not found"}), 404
    else:
        skeleton_instances, meta_info = load_skeleton_keypoint(file_path)
    client = OpenAI(
        api_key=qianfan_api_key,
        base_url="https://qianfan.baidubce.com/v2",
    )
    per_analysis = []

    batch_size = 5
    # for i in range(0, len(skeleton_instances), batch_size):
    for i in range(0, 20, batch_size):
        batch_instances = skeleton_instances[i : i + batch_size]

        # Build system prompt for the current batch of frames
        system_prompt = f"""
你是一个专业的乒乓球运动动作分析专家，擅长通过人体骨骼关键点坐标进行动作识别和姿态评估。请根据以下每帧图像中进行乒乓球对打时的人体骨骼点信息，结合字段说明，对前两个人的动作进行详细分析。分析内容应包括但不限于：

1. 动作是否规范（如站立、跑步、跳跃等是否符合常规标准）； 
2. 姿态是否稳定，是否存在不协调或危险的动作；
3. 动作幅度是否合理；
4. 如存在问题，请指出具体关键点及改进建议。

只为前两个人体进行分析，并且考虑到当前图像帧的编号，便于最后根据整体的运动轨迹进行分析。
输出标签使用：人体1、人体2
以下是骨骼点字段说明（metadata）： 
{meta_info}

以下是第 {i+1} 到 {min(i + batch_size, len(skeleton_instances))} 帧图像中的每个人体的骨骼点数据：
"""
        for j, skeleton_instance in enumerate(batch_instances):
            system_prompt += f"""
第 {i + j + 1} 帧图像中的每个人体的骨骼点数据： 
{skeleton_instance}
"""
        # Send the batch of frames to the OpenAI API for processing
        try:
            completion = client.chat.completions.create(
                model="deepseek-v3-241226",
                messages=[
                    {"role": "system", "content": "你是乒乓球运动动作分析专家"},
                    {"role": "user", "content": system_prompt},
                ],
                stream=False,
            )
            per_analysis.append(completion.choices[0].message.content)
            # print(completion.choices[0].message.content)
        except openai.RateLimitError:
            print("Rate limit exceeded. Waiting for 10 seconds...")
            time.sleep(10)
            completion = client.chat.completions.create(
                model="ernie-x1-32k-preview",
                messages=[
                    {"role": "system", "content": "你是乒乓球运动动作分析专家"},
                    {"role": "user", "content": system_prompt},
                ],
                stream=False,
            )
            per_analysis.append(completion.choices[0].message.content)
            # print(completion.choices[0].message.content)

    # After processing all batches, generate the final report
    final_prompt = f"""
你是一个专业的乒乓球运动动作分析专家，请根据以下每一帧的分析结果，对每个人的乒乓球动作进行独立分析并撰写报告。报告应包括但不限于以下内容：

1. **动作规范性评价**：该人的动作是否符合标准乒乓球动作要求。包括站位、击球动作、挥拍角度等是否标准。
2. **危险/异常动作**：是否存在不协调或危险的动作（例如：过度伸展、非正常的身体姿势等）。
3. **动作连贯性和节奏**：该人动作是否流畅，是否有停顿或节奏问题，动作的起始和结束是否平衡。
4. **改进建议**：如果动作中存在问题，请根据每一帧中的骨骼点分析给出改进的具体建议。
5. **综合评价**：结合整体运动表现，给出该人运动表现的总体评价。

### 以下是每一帧的分析内容，基于骨骼点数据和动作分析：
{per_analysis}

请为每个的运动员生成详细的报告，每个人的分析按以下格式输出：
- **运动员1**:
    - 动作规范性评价：
    - 危险/异常动作：
    - 动作连贯性和节奏：
    - 改进建议：
    - 综合评价：
- **运动员2**:
    - 动作规范性评价：
    - 危险/异常动作：
    - 动作连贯性和节奏：
    - 改进建议：
    - 综合评价：

请确保每个运动员的动作分析清晰且详细，最终输出每个运动员的综合表现和改进建议。
"""

    response = client.chat.completions.create(
        model="ernie-x1-32k-preview",
        messages=[
            {"role": "system", "content": "你是乒乓球运动动作分析专家"},
            {"role": "user", "content": final_prompt},
        ],
        stream=False,
    )
    return jsonify({"report": response.choices[0].message.content})


def auto_generate_report(file_path, user_id, filename):
    global _N, _report_paths  # 声明全局变量

    if not os.path.exists(file_path):
        return {"status": "error", "error": "File not found"}, 404
    else:
        skeleton_instances, meta_info = load_skeleton_keypoint(file_path)
    client = OpenAI(
        api_key=qianfan_api_key,
        base_url="https://qianfan.baidubce.com/v2",
    )
    per_analysis = []

    batch_size = 5
    # for i in range(0, len(skeleton_instances), batch_size):
    for i in range(0, 10, batch_size):
        batch_instances = skeleton_instances[i : i + batch_size]

        # Build system prompt for the current batch of frames
        system_prompt = f"""
你是一个专业的乒乓球运动动作分析专家，擅长通过人体骨骼关键点坐标进行动作识别和姿态评估。请根据以下每帧图像中进行乒乓球对打时的人体骨骼点信息，结合字段说明，对前两个人的动作进行详细分析。分析内容应包括但不限于：

1. 动作是否规范（如站立、跑步、跳跃等是否符合常规标准）； 
2. 姿态是否稳定，是否存在不协调或危险的动作；
3. 动作幅度是否合理；
4. 如存在问题，请指出具体关键点及改进建议。

只为前两个人体进行分析，并且考虑到当前图像帧的编号，便于最后根据整体的运动轨迹进行分析。
输出标签使用：人体1、人体2
以下是骨骼点字段说明（metadata）： 
{meta_info}

以下是第 {i+1} 到 {min(i + batch_size, len(skeleton_instances))} 帧图像中的每个人体的骨骼点数据：
"""
        for j, skeleton_instance in enumerate(batch_instances):
            system_prompt += f"""
第 {i + j + 1} 帧图像中的每个人体的骨骼点数据： 
{skeleton_instance}
"""
        # Send the batch of frames to the OpenAI API for processing
        try:
            completion = client.chat.completions.create(
                model="deepseek-v3-241226",
                messages=[
                    {"role": "system", "content": "你是乒乓球运动动作分析专家"},
                    {"role": "user", "content": system_prompt},
                ],
                stream=False,
            )
            per_analysis.append(completion.choices[0].message.content)
            # print(completion.choices[0].message.content)
        except openai.RateLimitError:
            print("Rate limit exceeded. Waiting for 10 seconds...")
            time.sleep(10)
            completion = client.chat.completions.create(
                model="ernie-x1-32k-preview",
                messages=[
                    {"role": "system", "content": "你是乒乓球运动动作分析专家"},
                    {"role": "user", "content": system_prompt},
                ],
                stream=False,
            )
            per_analysis.append(completion.choices[0].message.content)
            # print(completion.choices[0].message.content)

    # After processing all batches, generate the final report
    final_prompt = f"""
你是一个专业的乒乓球运动动作分析专家，请根据以下每一帧的分析结果，对每个人的乒乓球动作进行独立分析并撰写报告。报告应包括但不限于以下内容：

1. **动作规范性评价**：该人的动作是否符合标准乒乓球动作要求。包括站位、击球动作、挥拍角度等是否标准。
2. **危险/异常动作**：是否存在不协调或危险的动作（例如：过度伸展、非正常的身体姿势等）。
3. **动作连贯性和节奏**：该人动作是否流畅，是否有停顿或节奏问题，动作的起始和结束是否平衡。
4. **改进建议**：如果动作中存在问题，请根据每一帧中的骨骼点分析给出改进的具体建议。
5. **综合评价**：结合整体运动表现，给出该人运动表现的总体评价。

### 以下是每一帧的分析内容，基于骨骼点数据和动作分析：
{per_analysis}

请为每个的运动员生成详细的报告，每个人的分析按以下格式输出：
- **运动员1**:
    - 动作规范性评价：
    - 危险/异常动作：
    - 动作连贯性和节奏：
    - 改进建议：
    - 综合评价：
- **运动员2**:
    - 动作规范性评价：
    - 危险/异常动作：
    - 动作连贯性和节奏：
    - 改进建议：
    - 综合评价：

请确保每个运动员的动作分析清晰且详细，最终输出每个运动员的综合表现和改进建议。
"""

    response = client.chat.completions.create(
        model="ernie-x1-32k-preview",
        messages=[
            {"role": "system", "content": "你是乒乓球运动动作分析专家"},
            {"role": "user", "content": final_prompt},
        ],
        stream=False,
    )
    report = response.choices[0].message.content
    pose_user_dir = Path(BaseConfig.POSE_FOLDER) / f"user_{user_id}"
    with open(
        f"{pose_user_dir}/results_"
        + f"{os.path.splitext(os.path.basename(filename))[0]}.md",
        "w",
        encoding="utf-8",
    ) as f:
        f.write(report)

    _report_paths.append(
        f"{pose_user_dir}/results_"
        + f"{os.path.splitext(os.path.basename(filename))[0]}.md"
    )
    _N += 1
    return report

