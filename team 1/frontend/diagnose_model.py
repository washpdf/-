# diagnose_model.py

import onnx
import onnxruntime as ort
import numpy as np
import os

def diagnose_onnx_model(onnx_path="frontend/best.onnx"):
    """完整诊断 ONNX 模型"""
    
    print("="*60)
    print("ONNX 模型诊断工具")
    print("="*60)
    
    # 1. 检查文件是否存在
    if not os.path.exists(onnx_path):
        print(f"❌ 文件不存在: {onnx_path}")
        return False
    
    file_size = os.path.getsize(onnx_path) / 1024 / 1024
    print(f"✅ 文件存在: {onnx_path}")
    print(f"📦 文件大小: {file_size:.2f} MB")
    
    # 2. 检查文件头
    with open(onnx_path, 'rb') as f:
        header = f.read(8)
    print(f"🔍 文件头: {header.hex()}")
    
    # 正常的 ONNX 文件头应该是: 08 03 12 07
    if header[:4] == b'\x08\x03\x12\x07':
        print("✅ 文件头验证通过")
    else:
        print("❌ 文件头异常，文件可能损坏")
        return False
    
    # 3. 加载并检查模型结构
    try:
        model = onnx.load(onnx_path)
        onnx.checker.check_model(model)
        print("✅ ONNX 模型结构验证通过")
    except Exception as e:
        print(f"❌ 模型结构验证失败: {e}")
        return False
    
    # 4. 获取模型详细信息
    print("\n📊 模型详细信息:")
    print(f"   IR 版本: {model.ir_version}")
    print(f"   生产者: {model.producer_name}")
    print(f"   模型版本: {model.model_version}")
    print(f"   图名称: {model.graph.name}")
    
    # 5. 列出所有算子
    ops = set()
    for node in model.graph.node:
        ops.add(node.op_type)
    
    print(f"\n📋 使用的算子 ({len(ops)} 个):")
    print(f"   {', '.join(sorted(ops)[:20])}")
    if len(ops) > 20:
        print(f"   ... 共 {len(ops)} 个算子")
    
    # 6. 检查不支持的算子
    unsupported_ops = check_unsupported_operators(ops)
    if unsupported_ops:
        print(f"\n⚠️ 发现可能不支持的算子: {unsupported_ops}")
    else:
        print("\n✅ 所有算子都在支持范围内")
    
    # 7. 获取输入输出信息
    print("\n📥 输入信息:")
    for inp in model.graph.input:
        print(f"   名称: {inp.name}")
        shape = [dim.dim_value if dim.dim_value > 0 else '?' for dim in inp.type.tensor_type.shape.dim]
        print(f"   形状: {shape}")
    
    print("\n📤 输出信息:")
    for out in model.graph.output:
        print(f"   名称: {out.name}")
        shape = [dim.dim_value if dim.dim_value > 0 else '?' for dim in out.type.tensor_type.shape.dim]
        print(f"   形状: {shape}")
    
    # 8. 测试 ONNX Runtime (Python)
    print("\n🚀 测试 Python ONNX Runtime...")
    try:
        session = ort.InferenceSession(onnx_path, providers=['CPUExecutionProvider'])
        print("✅ Python ONNX Runtime 加载成功")
        
        # 获取输入形状
        input_name = session.get_inputs()[0].name
        input_shape = session.get_inputs()[0].shape
        
        # 创建测试数据
        test_shape = list(input_shape)
        for i in range(len(test_shape)):
            if test_shape[i] is None or test_shape[i] == 0 or test_shape[i] == '?':
                if i == 0:
                    test_shape[i] = 1
                elif i == 2 or i == 3:
                    test_shape[i] = 640
                else:
                    test_shape[i] = 1
        
        test_input = np.random.randn(*test_shape).astype(np.float32)
        outputs = session.run(None, {input_name: test_input})
        print(f"✅ 推理成功，输出形状: {outputs[0].shape}")
        
    except Exception as e:
        print(f"❌ Python ONNX Runtime 测试失败: {e}")
        return False
    
    print("\n" + "="*60)
    print("🎉 模型在 Python 端可用！")
    print("⚠️ 如果浏览器仍无法加载，需要简化模型")
    print("="*60)
    
    return True

def check_unsupported_operators(ops):
    """检查不支持的算子"""
    
    # ONNX Runtime Web 不完全支持的算子
    problematic_ops = {
        'Resize', 'Upsample', 'GridSampler', 'NonMaxSuppression',
        'RoiAlign', 'Multinomial', 'RandomNormal', 'RandomUniform',
        'EyeLike', 'OneHot', 'TopK', 'Unique', 'Where'
    }
    
    # 需要特定实现的算子
    limited_ops = {
        'Softmax': '需要指定 axis',
        'ConvTranspose': '某些配置不支持',
        'MaxPool': 'ceil_mode=True 可能有问题'
    }
    
    unsupported = ops.intersection(problematic_ops)
    
    return unsupported if unsupported else None

if __name__ == "__main__":
    # 诊断模型
    diagnose_onnx_model("best.onnx")