#!/usr/bin/env python3
"""
启动Gateway和API服务器的脚本
使用uvicorn启动两个FastAPI应用
"""

import multiprocessing
import os
import signal
import sys
import time

import uvicorn


def start_api_server(
    host: str = "127.0.0.1", port: int = 8000, reload: bool = False
):
    """启动API服务器"""
    # 设置Python路径
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    print(f"🚀 启动API服务器在 http://{host}:{port}")
    config = uvicorn.Config(
        "myunla.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
        access_log=True,
    )
    server = uvicorn.Server(config)
    server.run()


def start_gateway_server(
    host: str = "127.0.0.1", port: int = 8001, reload: bool = False
):
    """启动Gateway服务器"""
    # 设置Python路径
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    print(f"🚀 启动Gateway服务器在 http://{host}:{port}")

    # 创建Gateway应用实例
    from myunla.config import gateway_settings
    from myunla.gateway.server import GatewayServer
    from myunla.gateway.state import Metrics, State

    gateway_server = GatewayServer(
        State(
            mcps=[],
            runtime={},
            metrics=Metrics(),
        ),
        gateway_settings["session_config"],
    )

    config = uvicorn.Config(
        gateway_server.app,
        host=host,
        port=port,
        reload=reload,
        log_level="info",
        access_log=True,
    )
    server = uvicorn.Server(config)
    server.run()


def signal_handler(signum, frame):
    """信号处理器，用于优雅地关闭服务器"""
    print("\n⚠️  收到终止信号，正在关闭服务器...")
    sys.exit(0)


def main():
    """主函数"""
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 配置参数
    api_host = "127.0.0.1"
    api_port = 8000
    gateway_host = "127.0.0.1"
    gateway_port = 8001
    reload_mode = "--reload" in sys.argv or "-r" in sys.argv

    print("=" * 60)
    print("🎯 MyUnla 服务器启动器")
    print("=" * 60)
    print(f"📡 API服务器地址: http://{api_host}:{api_port}")
    print(f"🌐 Gateway服务器地址: http://{gateway_host}:{gateway_port}")
    print(f"🔄 热重载模式: {'启用' if reload_mode else '禁用'}")
    print("=" * 60)

    try:
        # 创建并启动进程
        api_process = multiprocessing.Process(
            target=start_api_server,
            args=(api_host, api_port, reload_mode),
            name="api-server",
        )

        gateway_process = multiprocessing.Process(
            target=start_gateway_server,
            args=(gateway_host, gateway_port, reload_mode),
            name="gateway-server",
        )

        # 启动进程
        api_process.start()
        time.sleep(1)  # 稍微延迟启动gateway
        gateway_process.start()

        print("✅ 所有服务器已启动!")
        print("📋 使用 Ctrl+C 来停止所有服务器")
        print()

        # 等待进程完成
        api_process.join()
        gateway_process.join()

    except KeyboardInterrupt:
        print("\n⚠️  收到中断信号，正在关闭服务器...")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
    finally:
        # 确保进程被清理
        if 'api_process' in locals() and api_process.is_alive():
            print("🔄 正在停止API服务器...")
            api_process.terminate()
            api_process.join(timeout=5)
            if api_process.is_alive():
                api_process.kill()

        if 'gateway_process' in locals() and gateway_process.is_alive():
            print("🔄 正在停止Gateway服务器...")
            gateway_process.terminate()
            gateway_process.join(timeout=5)
            if gateway_process.is_alive():
                gateway_process.kill()

        print("✅ 所有服务器已停止")


if __name__ == "__main__":
    # 设置多进程启动方式（解决某些平台的兼容性问题）
    if sys.platform != "win32":
        multiprocessing.set_start_method('fork', force=True)
    else:
        multiprocessing.set_start_method('spawn', force=True)
    main()
