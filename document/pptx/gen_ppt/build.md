# 执行脚本生成 .pptx 文件

工具返回输出目录路径后，使用 `jupyter_cell_exec`工具 执行生成的脚本：

```python
import subprocess, os, sys

script_dir = "<工具返回的输出目录>"
script_path = os.path.join(script_dir, "build_pptx.py")
result = subprocess.run([sys.executable, script_path], capture_output=True, text=True, cwd=script_dir)
print(result.stdout)
if result.returncode != 0:
    print("STDERR:", result.stderr)
```

执行成功后，`.pptx` 文件会保存在脚本所在目录下，文件名与 `<FileName>` 一致。
