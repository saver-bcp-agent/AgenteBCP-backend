from agent import process_message  # Importa la función desde tu agente

def test_console():
    print("Bienvenido al chatbot. Escribe 'salir' para terminar.\n")
    
    while True:
        user_input = input("Tú: ")  # Captura el mensaje del usuario
        
        if user_input.lower() == "salir":
            print("Chat finalizado.")
            break
        
        response = process_message(1,user_input)  # Llama a la función del agente
        print(f"Bot: {response}")  # Muestra la respuesta del chatbot

if __name__ == "__main__":
    test_console()