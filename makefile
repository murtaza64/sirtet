tetris: *.py
	@echo "I used Q-learning to create a simple Tetris player. It does OK--I've seen it score a few thousand, but nowhere close to what a human player could get in the time it took to program this. You can watch it play here--as long as your terminal has curses support. Press any key to continue."
	@echo "To run it, please run 'make play' or python3 game.py"

make play: *.py
	python3 game.py