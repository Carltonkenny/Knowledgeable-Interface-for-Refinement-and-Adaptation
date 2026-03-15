import sys
sys.path.append('.')
import database
import inspect

with open('db_funcs.txt', 'w') as f:
    functions_to_inspect = [
        'get_chat_sessions',
        'get_deleted_sessions',
        'update_chat_session',
        'create_chat_session',
        'delete_chat_session',
        'purge_chat_session',
        'restore_chat_session'
    ]
    
    for name in functions_to_inspect:
        f.write(f"--- {name} ---\n")
        if hasattr(database, name):
            try:
                f.write(inspect.getsource(getattr(database, name)))
            except Exception as e:
                f.write(f"Error inspecting: {e}\n")
            f.write("\n\n")
        else:
            f.write("Missing\n\n")
print("Inspection complete. Saved to db_funcs.txt")
