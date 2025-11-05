from PIL import Image

def text_to_bin(text):
    return ''.join(format(ord(c), '08b') for c in text)

def bin_to_text(binary):
    chars = [binary[i:i+8] for i in range(0, len(binary), 8)]
    return ''.join(chr(int(c, 2)) for c in chars)

def embed_message(image_path, message, output_path):
    img = Image.open(image_path)
    img = img.convert('RGB')
    binary_message = text_to_bin(message) + '1111111111111110'
    data_index = 0

    pixels = list(img.getdata())
    new_pixels = []

    for pixel in pixels:
        r, g, b = pixel
        if data_index < len(binary_message):
            r = (r & ~1) | int(binary_message[data_index])
            data_index += 1
        if data_index < len(binary_message):
            g = (g & ~1) | int(binary_message[data_index])
            data_index += 1
        if data_index < len(binary_message):
            b = (b & ~1) | int(binary_message[data_index])
            data_index += 1
        new_pixels.append((r, g, b))

    img.putdata(new_pixels)
    img.save(output_path)
    print(f"Сообщение внедрено в {output_path}")

def extract_message(image_path):
    img = Image.open(image_path)
    img = img.convert('RGB')
    pixels = list(img.getdata())

    binary_message = ""
    for pixel in pixels:
        r, g, b = pixel
        binary_message += str(r & 1)
        binary_message += str(g & 1)
        binary_message += str(b & 1)

    binary_message = binary_message.split('1111111111111110')[0]
    return bin_to_text(binary_message)

if __name__ == "__main__":
    input_image = "Снимок экрана 2025-11-05 134251.bmp"
    output_image = "output.bmp"
    message = input("Сообщение для внедрения: ")

    embed_message(input_image, message, output_image)
    extracted = extract_message(output_image)
    print("Извлечённое сообщение:", extracted)