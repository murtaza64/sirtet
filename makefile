tetris: *.py
	@echo "I used Q-learning to create a simple Tetris player. \
	It does OK--I've seen it score a few thousand, but nowhere close \
	to what a human player could get in the time it took to program this. \
	You can watch it play here--as long as your terminal has curses support."
	@echo "Usage:"
	@echo "make play        run the tetris simulator and AI framework (requires curses)"
	@echo "                 (stderr from threads will be piped to stderr.out)"

make play: *.py
	python3 game.py 2> stderr.out