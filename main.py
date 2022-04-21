from fastapi import FastAPI, Response, Request, Cookie, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials, api_key
from typing import Optional
from pydantic import BaseModel
from datetime import timedelta, date
import hashlib
import secrets
import sqlite3


app = FastAPI()
# uvicorn main:app
app.counter = 0
app.id = 0
patients = []


class HelloResp(BaseModel):
    msg: str


class Patient(BaseModel):
    name: str
    surname: str


class PatientInfo:
    id: int
    name: str
    surname: str
    register_date: str
    vaccination_date: str


class Category(BaseModel):
    name: str


@app.get("/")
def root():
    return {"message": "Hello world!"}


@app.get("/check")
def check(password, password_hash):
    pass


@app.get("/hello/{name}")
async def hello_name_view(name: str):
    return f"Hello {name}"


@app.get("/counter")
def counter():
    app.counter += 1
    return app.counter


@app.get("/hello/{name}")
async def read_item(name: str):
    return HelloResp(msg=f"Hello {name}")


@app.get("/method")
def method(request: Request, response: Response):
    met = request.method
    if met == "POST":
        response.status_code = 201
    return {"method": met}


@app.post("/method")
def method(request: Request, response: Response):
    met = request.method
    if met == "POST":
        response.status_code = 201
    return {"method": met}


@app.put("/method")
def method(request: Request, response: Response):
    met = request.method
    if met == "POST":
        response.status_code = 201
    return {"method": met}


@app.delete("/method")
def method(request: Request, response: Response):
    met = request.method
    if met == "POST":
        response.status_code = 201
    return {"method": met}


@app.options("/method")
def method(request: Request, response: Response):
    met = request.method
    if met == "POST":
        response.status_code = 201
    return {"method": met}


@app.get("/auth")
async def auth(response: Response, password: Optional[str] = "", password_hash: Optional[str] = ""):

    if password == "" or password_hash == "":
        response.status_code = 401
        return HTMLResponse(status_code=response.status_code)
    m = hashlib.sha512()
    m.update(bytes(password, 'utf-8'))
    if m.hexdigest() == password_hash:
        response.status_code = 204
    else:
        response.status_code = 401
    return HTMLResponse(status_code=response.status_code)


@app.post("/register")
def register(patient: Patient, response: Response):
    app.id += 1
    register_date = date.today()

    def letter_count(text: str):
        count = 0
        for sign in text:
            if sign.isalpha():
                count += 1
        return count
    add_days = letter_count(patient.name) + letter_count(patient.surname)
    vaccination_date = (register_date + timedelta(days=add_days))

    patient_info = PatientInfo()
    patient_info.id = app.id
    patient_info.name = patient.name
    patient_info.surname = patient.surname
    patient_info.register_date = register_date.isoformat()
    patient_info.vaccination_date = vaccination_date.isoformat()
    patients.append(patient_info)
    response.status_code = 201
    return patient_info


@app.get("/patient/{id}")
def get_patient(id: int):
    if id < 1:
        return HTMLResponse(status_code=400)
    for p in patients:
        if p.id == id:
            return {"id": p.id,
                    "name": p.name,
                    "surname": p.surname,
                    "register_date": p.register_date,
                    "vaccination_date": p.vaccination_date}
    return HTMLResponse(status_code=404)


@app.get("/hello", response_class=HTMLResponse)
def hello():
    today_date = date.today().isoformat()
    return f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Hello</title>
    </head>
    <body>
        <h1>Hello! Today date is {today_date}</h1>
    </body>
    </html>
    """


_user = "4dm1n"
_password = "NotSoSecurePa$$"
security = HTTPBasic()
app.sessions = []
app.logins = []
app.last_session_token = ""
app.last_login_token = ""


@app.post("/login_session")
def login_session(response: Response, credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, _user)
    correct_password = secrets.compare_digest(credentials.password, _password)
    if not (correct_username and correct_password):
        raise HTTPException(status_code=401)
    token = secrets.token_hex(10)
    app.last_session_token = token
    if len(app.sessions) == 3:
        del app.sessions[0]
    app.sessions.append(token)
    response.status_code = 201
    response.set_cookie(key="session_token", value=token)
    return {"username": credentials.username, "password": credentials.password, "token": token}


@app.post("/login_token")
def login_token(response: Response, credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, _user)
    correct_password = secrets.compare_digest(credentials.password, _password)
    if not (correct_username and correct_password):
        raise HTTPException(status_code=401)
    login_token = secrets.token_hex(10)
    app.last_login_token = login_token
    if len(app.logins) == 3:
        del app.logins[0]
    app.logins.append(login_token)
    response.status_code = 201
    return {"token": login_token}


@app.get("/welcome_session")
def welcome_session(format: Optional[str] = "", session_token: str = Cookie(None)):
    if session_token not in app.sessions:
        print(session_token, app.sessions)
        raise HTTPException(status_code=401)
    if format == "json":
        return JSONResponse(content={"message": "Welcome!"})
    elif format == "html":
        return HTMLResponse(content="<h1>Welcome!</h1>")
    else:
        return PlainTextResponse("Welcome!")


@app.get("/welcome_token")
def welcome_token(token: Optional[str] = "", format: Optional[str] = ""):
    if token not in app.logins or token == "":
        print(token, app.logins)
        raise HTTPException(status_code=401)
    if format == "json":
        return JSONResponse(content={"message": "Welcome!"})
    elif format == "html":
        return HTMLResponse(content="<h1>Welcome!</h1>")
    else:
        return PlainTextResponse("Welcome!")


@app.delete("/logout_session")
def logout_session(session_token: str = Cookie(None), format: Optional[str] = ""):
    if session_token not in app.sessions:
        print(session_token, app.sessions)
        raise HTTPException(status_code=401)
    app.last_session_token = ""
    app.sessions.remove(session_token)
    url = "/logged_out?format=" + format
    return RedirectResponse(url=url, status_code=303)


@app.delete("/logout_token")
def logout_token(token: Optional[str] = "", format: Optional[str] = ""):
    if token not in app.logins or token == "":
        print(token, app.logins)
        raise HTTPException(status_code=401)
    app.last_login_token = ""
    print(token)
    app.logins.remove(token)
    url = "/logged_out?format=" + format
    return RedirectResponse(url=url, status_code=303)


@app.get("/logged_out")
def logged_out(format: Optional[str] = ""):
    if format == "json":
        return JSONResponse(content={"message": "Logged out!"})
    elif format == "html":
        return HTMLResponse(content="<h1>Logged out!</h1>")
    else:
        return PlainTextResponse("Logged out!")
#######################################################
# 4


app.db_connection = None


@app.on_event("startup")
async def startup():
    app.db_connection = sqlite3.connect("northwind.db")
    app.db_connection.text_factory = lambda b: b.decode(errors="ignore", encoding = "ISO 8859-1")  # northwind specific


@app.on_event("shutdown")
async def shutdown():
    app.db_connection.close()


@app.get("/categories")
async def categories():
    categories = app.db_connection.execute("SELECT CategoryID, CategoryName FROM Categories ORDER BY CategoryID").fetchall()
    message = []
    for cat in categories:
        message.append({"id": cat[0], "name": cat[1]})
    return {
        "categories": message
    }


@app.get("/customers")
async def customers():
    customers = app.db_connection.execute("SELECT CustomerID, CompanyName, COALESCE(Address, '') || ' ' || COALESCE(PostalCode,'') || ' ' || COALESCE(City, '') || ' ' || COALESCE(Country, '') FROM Customers ORDER BY LOWER(CustomerID)").fetchall()
    message = []
    for cust in customers:
        message.append({"id": cust[0], "name": cust[1], "full_address": cust[2]})
    return {"customers": message}


@app.get("/products/{id}")
async def products_id(id: int):
    all_ids = app.db_connection.execute("SELECT ProductID FROM Products").fetchall()
    all_ids_list = [identifier for ident_list in all_ids for identifier in ident_list]
    if id not in all_ids_list:
        raise HTTPException(status_code=404)
    product = app.db_connection.execute(f"SELECT ProductID, ProductName FROM Products WHERE ProductID={id}").fetchall()
    return {"id": product[0][0], "name": product[0][1]}


@app.get("/employees")
async def employees(limit: Optional[int] = 0, offset: Optional[int] = 0, order: Optional[str] = ""):
    settings = {"limit":"", 'offset':"", "order": ""}
    order_dict = {"id": "EmployeeID", "last_name": "LastName", "first_name": "FirstName", "city": "City"}
    if limit > 0:
        settings["limit"] = f" LIMIT {limit}"
    if offset > 0:
        settings["offset"]=f" OFFSET {offset}"
    if order != "":
        if order not in list(order_dict.keys()):
            raise HTTPException(status_code=400)
        settings["order"] = f" ORDER BY {order_dict[order]}"
    empls = app.db_connection.execute(f"SELECT EmployeeID, LastName, FirstName, City FROM Employees{settings['order']}{settings['limit']}{settings['offset']}").fetchall()
    message = []
    for e in empls:
        message.append({"id": e[0], "last_name": e[1], "first_name": e[2], "city": e[3]})
    return {"employees": message}


@app.get("/products_extended")
async def products_extended():
    products = app.db_connection.execute("SELECT ProductID, ProductName, CategoryName, CompanyName FROM Products JOIN Categories ON Products.CategoryID = Categories.CategoryID JOIN Suppliers ON Products.SupplierID = Suppliers.SupplierID ORDER BY ProductID").fetchall()
    message = []
    for product in products:
        message.append({"id": product[0], "name": product[1], "category": product[2], "supplier": product[3]})
    return {"products_extended": message}


@app.get("/products/{id}/orders")
async def product_orders(id: int):
    all_ids = app.db_connection.execute("SELECT ProductID FROM Products").fetchall()
    all_ids_list = [identifier for ident_list in all_ids for identifier in ident_list]
    if id not in all_ids_list:
        raise HTTPException(status_code=404)
    orders = app.db_connection.execute(f"SELECT Orders.OrderID, CompanyName, Quantity, 'Order Details'.UnitPrice, Discount, 'Order Details'.ProductID FROM Orders JOIN Customers ON Orders.CustomerID = Customers.CustomerID JOIN 'Order Details' ON Orders.OrderID='Order Details'.OrderID WHERE 'Order Details'.ProductID = {id} ORDER BY Orders.OrderID").fetchall()
    message = []
    for order in orders:
        price = order[2]*order[3] * (1-order[4])
        message.append({"id": order[0], "customer": order[1], "quantity": order[2], "total_price": price.__round__(2)})
    return {"orders": message}


@app.post("/categories", status_code=201)
async def categories(category: Category):
    last_id = app.db_connection.execute("SELECT CategoryID FROM Categories ORDER BY CategoryID DESC LIMIT 1").fetchone()[0]
    app.db_connection.execute(f"INSERT INTO Categories (CategoryID, CategoryName) VALUES ({last_id+1}, '{category.name}');")
    message = app.db_connection.execute(f"SELECT CategoryID, CategoryName FROM Categories WHERE CategoryID = {last_id+1}").fetchall()
    return {"id": message[0][0], "name": message[0][1]}


@app.put("/categories/{id}")
async def categories_update(id: int, category: Category):
    all_ids = app.db_connection.execute("SELECT CategoryID FROM Categories").fetchall()
    all_ids_list = [identifier for ids_list in all_ids for identifier in ids_list]
    if id not in all_ids_list:
        raise HTTPException(status_code=404)
    app.db_connection.execute(f"UPDATE Categories SET CategoryName = '{category.name}' WHERE CategoryID = {id}")
    response = app.db_connection.execute(f"SELECT CategoryID, CategoryName FROM Categories WHERE CategoryID = {id}").fetchall()
    return {"id": response[0][0], "name": response[0][1]}


@app.delete("/categories/{id}", status_code=200)
async def categories_delete(id: int):
    all_ids = app.db_connection.execute(f"SELECT CategoryID FROM Categories").fetchall()
    all_ids_list = [identifier for ids_list in all_ids for identifier in ids_list]
    if id not in all_ids_list:
        raise HTTPException(status_code=404)
    app.db_connection.execute(f"DELETE FROM Categories WHERE CategoryID ={id}")
    return {"deleted": 1}


@app.get("/products")
async def products():
    _products = app.db_connection.execute("SELECT ProductName FROM Products").fetchall()
    return {
        "products": list(map(lambda x: x[0], _products)),
        "products_counter": len(_products)
    }


@app.get("/test/{ttt}")
def test(request: Request, ttt: float):

    return ttt, request.query_params


@app.get("/items/")
def read_items(*, ads_id: str = Cookie(None)):
    return {"ads_id": ads_id}
