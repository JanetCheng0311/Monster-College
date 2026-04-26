import sys
from tetris_game import Tetris

if __name__ == '__main__':
    # pygbag will initialize Pygame; create and run the game normally.
    game = Tetris(None)
    try:
        # Tetris class uses instance methods; run the main loop by calling a simple driver.
        # The original module exposes run via constructing and running in its __main__ path.
        # Here we call a minimal loop: if module has a run-like API, adapt accordingly.
        # For compatibility, try to call a `run` function if present; otherwise run Tetris instance methods.
        if hasattr(sys.modules.get('tetris_game'), 'main'):
            # Some modules define main(); call it.
            sys.modules['tetris_game'].main()
        else:
            # Fallback: start the game loop by calling the Tetris instance run loop if defined.
            # The Tetris class in the original file uses methods on the instance; we'll try to call run() if present.
            if hasattr(game, 'run'):
                game.run()
            else:
                # If no run method, attempt to start the pygame loop by calling main()
                try:
                    from tetris_game import main as tg_main
                    tg_main()
                except Exception:
                    raise RuntimeError('Unable to start Tetris in the web environment.')
    except Exception as e:
        print('Failed to start prototype Tetris:', e)
        raise
