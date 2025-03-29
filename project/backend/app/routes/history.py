from flask import jsonify, request, Blueprint
from ..utils.security import jwt_required

history_bp = Blueprint('history', __name__)

HISTORY_DATA = [
    {
        "id": 1,
        "time": "2019-01-10 12:24:22",
        "status": "expired",
        "expiry": "2024-03-20",
    },
    {
        "id": 2,
        "time": "2024-1-20 12:24:22",
        "status": "processing",
        "expiry": "2024-03-20",
    },
    {
        "id": 3,
        "time": "2024-09-20 12:24:22",
        "status": "completed",
        "expiry": "2024-03-20",
    },
    # 其他数据...
]

@history_bp.route('/history', methods=['GET', 'DELETE'])
@jwt_required
def handle_history():
    global HISTORY_DATA

    if request.method == 'GET':
        try:
            return jsonify({
                "success": True,
                "data": HISTORY_DATA  # 确保返回结构包含 data 字段
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "message": "获取历史记录失败"
            }), 500

    elif request.method == 'DELETE':
        data = request.get_json()
        item_id = data.get('id')

        # 校验 id 是否存在且有效
        if not item_id:
            return jsonify({
                "success": False,
                "message": "缺少参数 id"
            }), 400

        # 确保 id 是整数
        try:
            item_id = int(item_id)
        except ValueError:
            return jsonify({
                "success": False,
                "message": "无效的 id 格式"
            }), 400

        # 检查要删除的项是否存在
        original_length = len(HISTORY_DATA)
        HISTORY_DATA = [item for item in HISTORY_DATA if item['id'] != item_id]

        if len(HISTORY_DATA) == original_length:
            return jsonify({
                "success": False,
                "message": "未找到对应记录"
            }), 404

        return jsonify({
            "success": True,
            "message": "删除成功"
        })