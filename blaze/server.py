import io
import sys
import socket

from datetime import datetime
from typing import Literal



PORT: int = 8080
ADDRESS: Literal[''] = ""
SERVER_ADDRESS: tuple[Literal[''], Literal[8080]] = (ADDRESS, PORT)


class Blaze():

    address_family: socket.AddressFamily = socket.AF_INET
    socket_type: socket.SocketKind = socket.SOCK_STREAM
    request_queue_size = 1

    def __init__(self, client_address, wsgi_app) -> None:
        """
            Creating socket and making it listen.
        """
        try:
            self.sock_obj = sock_obj = socket.socket(
                self.address_family, self.socket_type,)

            sock_obj.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            sock_obj.bind(client_address)

            sock_obj.listen(self.request_queue_size)

            host, port = self.sock_obj.getsockname()

            self.server_port = port
            self.server_name = socket.getfqdn(host)
            self.application = wsgi_app

        except OSError:
            sys.exit(f"Error: Port {PORT} is already in use.")

    def run_server(self) -> None:
        """
            Continuously Accepts the Incoming Request
        """
        while True:
            client_connection, request_address = self.sock_obj.accept()
            self.client_connection = client_connection
            self.handle_request(client_connection)  

    def handle_request(self, connection: socket.socket) -> None:
        """
            Recieves the Incoming Request
        """
        try:
            client_request_data: bytes = connection.recv(1024)
            self.request_data: str = client_request_data.decode("utf-8")

            self.parse_request_data(self.request_data)

            env = self.get_environ()

            result = self.application(env, self.get_response)

            self.finish_response(result)
        except Exception as ex:
            print(ex)

    def parse_request_data(self, request_data: str) -> None:

        request_info: str = request_data.splitlines()[0]
        # Break down the request_info into components
        (self.request_method,  # GET
         self.path,            # /hello
         self.request_version  # HTTP/1.1
         ) = request_info.split()

    def finish_response(self, result):

        try:
            status, response_headers = self.headers_set
            response: str = f'HTTP/1.1 {status}\r\n'
            log_response: str = f'HTTP/1.1 {status}'
            for header in response_headers:
                response += '{0}: {1}\r\n'.format(*header)
            response += '\r\n'
            for data in result:
                response += data.decode('utf-8')

            date_time = self.current_datetime.strftime('%H:%M:%S')

            print(f"{date_time} - {self.request_method}\n{log_response} - {self.path}\r\n")

            response_bytes = response.encode()

            self.client_connection.sendall(response_bytes)
        finally:
            self.client_connection.close()

    def get_environ(self) -> dict:
        """
            Returns the Environment Dictionary for the WSGI Application
        """
        env = {}
        env['wsgi.version'] = (1, 0)
        env['wsgi.url_scheme'] = 'http'
        env['wsgi.input'] = io.StringIO(self.request_data)
        env['wsgi.errors'] = sys.stderr
        # env['wsgi.multithread']  = False
        # env['wsgi.multiprocess'] = False
        # env['wsgi.run_once']     = False
        # Required CGI variables
        env['REQUEST_METHOD'] = self.request_method
        env['PATH_INFO'] = self.path
        env['SERVER_NAME'] = self.server_name
        env['SERVER_PORT'] = str(self.server_port)
        return env

    def get_response(self, status, response_headers) -> None:
        """
            Application Callable
            Adding necessary headers
        """
        self.current_datetime: datetime = datetime.utcnow()
        formatted_date: str = self.current_datetime.strftime(
            '%a, %d %b %Y %H:%M:%S UTC')

        server_headers = [
            ('Date', formatted_date),
            ('Server', 'Blaze 0.1'),
        ]
        self.headers_set = [status, response_headers + server_headers]


def create_new_server(client_address, wsgi_app) -> Blaze:
    """
        Creates a new Blaze Server Object
    """
    blaze = Blaze(client_address, wsgi_app)
    return blaze





if __name__ == '__main__':

    arguements: list[str] = sys.argv

    if len(arguements) < 2:
        sys.exit("Please provide WSGI objeect like module:app_callable")

    application_path: str = arguements[1]
    module, app_name = application_path.split(":")
    module = __import__(module)
    
    # Fetches the WSGI object from the Wsgi Framework.
    wsgi_obj = getattr(module, app_name)
    blaze_server: Blaze = create_new_server(SERVER_ADDRESS, wsgi_obj)
    print(f"\nRunning Blaze Server on Port {PORT}\r\n")
    blaze_server.run_server()
