from tensorflow import keras

MAX_SYMBOLS = 11
CELL_PX = 16


def build_cell_decoder(max_symbols: int = MAX_SYMBOLS) -> keras.Model:
    inputs = keras.Input(shape=(None, None, 3))
    hidden = keras.layers.Conv2D(16, 3, padding="same", activation="relu")(inputs)
    for filters in (16, 24, 32, 32):
        hidden = keras.layers.Conv2D(filters, 3, strides=2, padding="same", activation="relu")(hidden)
    logits = keras.layers.Conv2D(max_symbols, 1, padding="same", name="logits")(hidden)
    offset = keras.layers.Conv2D(2, 1, padding="same", activation="tanh", name="offset")(hidden)
    return keras.Model(inputs, [logits, offset])
