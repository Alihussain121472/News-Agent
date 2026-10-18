import sys
try:
    import web_server
    print('web_server imported successfully')
except Exception as e:
    print(f'Error importing web_server: {e}')
    import traceback
    traceback.print_exc()
