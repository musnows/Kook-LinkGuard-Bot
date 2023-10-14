.PHONY:run
run:
	nohup python3.10 -u lgbot.py >> /dev/null 2>&1 &

.PHONY:ps
ps:
	ps jax | head -1 && ps jax | grep lgbot.py | grep -v grep