import werkzeug
from flask import Flask, render_template, url_for, request, flash, g, redirect
import utils
import yagmail as yagmail
import os
from flask import session
from db import get_db
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import argparse

app = Flask(__name__)
app.static_folder = 'static'
app.secret_key = os.urandom( 24 )
app.config['UPLOAD_FOLDER'] = './static/img/imgProductos'

#Inicio de sesión - TEMPLATE
@app.route('/')
def login():
    try:
        if session['rol'] == 1:
            return redirect(url_for("inicio_administrador"))
        elif session['rol'] == 0:
            return redirect(url_for("inicio_usuario"))
    except:
        return render_template("iniciar_sesion.html")


#Backend de Inicio de Sesion
@app.route('/inicio', methods=('GET', 'POST'))
def inicio():
    try:
        if request.method == 'POST':
            db = get_db()
            error = None
            username = request.form['usuario_registrado']
            password = request.form['contraseña_registrada']
            user = db.execute('SELECT * FROM usuarios WHERE usuario = ?', (username,)).fetchone()

            if user is None:
                flash("Usuario o contraseña inválidos")
                return render_template('iniciar_sesion.html')
            else:
                claveBD = user[4]
                claveCorrecta = werkzeug.security.check_password_hash(claveBD, password)
                if claveCorrecta:
                    rol = user[5]

                    if rol:
                        session['userName'] = request.form['usuario_registrado']
                        session['idUser'] = user[0]
                        session['name'] = user[1]
                        session['email'] = user[3]
                        session['rol'] = user[5]
                        return redirect(url_for("inicio_administrador"))
                    else:
                        session['userName'] = request.form['usuario_registrado']
                        session['idUser'] = user[0]
                        session['name'] = user[1]
                        session['email'] = user[3]
                        session['rol'] = user[5]
                        return redirect(url_for("inicio_usuario"))
                else:
                    flash("Usuario o contraseña inválidos")
                    return render_template('iniciar_sesion.html')
    except:
        return render_template('iniciar_sesion.html')


#Cerrar sesión
@app.route('/logout', methods=('GET', 'POST'))
def logout(): # elimina el nombre de usuario de la sesión si está allí
    session.pop('userName', None)
    session.pop('name', None)
    session.pop('email', None)
    session.pop('rol', None)
    return render_template('iniciar_sesion.html')


#Solicitud de Registro - Template
@app.route('/formulario')
def formulario():
    return render_template("formulario_registro.html")


#Backend Solicitud de Registro
@app.route('/solicitud', methods=('GET', 'POST'))
def solicitud_registro():
    try:
        if request.method == 'POST':
            name = request.form['nombre']
            username = request.form['usuario']
            email = request.form['correo']
            password = request.form['contraseña']

            if not utils.isUsernameValid(username):
                flash("Nombre de usuario inválido")
                return render_template('formulario_registro.html')

            if not utils.isPasswordValid(password):
                flash("La contraseña debe contener al menos una minúscula, una mayúscula, un número y 8 caracteres")
                return render_template('formulario_registro.html')

            if not utils.isEmailValid(email):
                flash("Correo inválido")
                return render_template('formulario_registro.html')

            mensaje = "<html>" \
                      "<head><center><title>SOLICITUD PARA REGISTRO DE USUARIO</title></center></head>" \
                      "<body style='background: #DCDCDC;>" \
                      "<center><h1 style='font-weight: bold;' ></h1></center>" \
                      "<center><div style='width:450px; background: white; border-radius:5px;'>" \
                      "<img src='https://i.ibb.co/x8ns2tq/HANDMADE.png' style='width:450px; height:100px'><br><br>" \
                      "Cordial Saludo <br><br>" \
                      "Se ha Registrado una nueva solicitud de Registro en la plataforma<br><br>" \
                      "Los datos del usuario son los siguientes:<br><br>" \
                      "Nombre: <strong>" + name + "</strong><br>"\
                      "Username: <strong>" + username + "</strong><br>"\
                      "Correo: <strong>" + email + "</strong><br>"\
                      "Contraseña: <strong>" + password + "</strong><br><br>"\
                      "Para acceder al sistema, lo podra hacer mediante el siguiente enlace: <a href='https://54.227.121.118/administrador/registrar_usuario' style='font-weight: bold;'> INGRESAR </a><br><br>" \
                      "<div style='background-color:rgb(235,99,107);  height:20px; width: 450px;'></div>" \
                      "</div></center>" \
                      "</body>" \
                      "</html>"

            yag = yagmail.SMTP('handmadeJewellery20202@gmail.com', 'handmade2020')
            yag.send(to='handmadeJewellery20202@gmail.com', subject='SOLICITUD DE REGISTRO', contents=mensaje)

            flash("Su solicitud de registro será evaluada. Al correo registrado le llegará una notificación cuando su cuenta se active.")
            return render_template('formulario_registro.html')
        return render_template('formulario_registro.html')
    except:
        return render_template('formulario_registro.html')


@app.route('/consultainventario',methods=('GET', 'POST'))
def consulta():

    db = get_db()
    inventario = db.execute('SELECT * FROM accesorio').fetchall()
    return render_template('datatable.html', inventario=inventario)


@app.route("/<usr>")
def user(usr):
    return render_template('cambiar_contraseña.html')


@app.route("/administrador/registro_producto", methods=('GET', 'POST'))
def registroproducto():
    try:
        if request.method == 'POST':
            db = get_db()
            error = None
            referencia = request.form['referencia']
            nombre = request.form['nombre']
            cantidad = request.form['cantidad']
            tipo = request.form['tipo']
            f = request.files['archivo']
            filename = secure_filename(f.filename)
            # Guardamos el archivo en el directorio "Archivos PDF"
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            state = 'Activo'
            #imagen = parser.add_argument('picture', type=werkzeug.datastructures.FileStorage, location='files')

            if db.execute('SELECT id FROM accesorio WHERE referencia = ?', (referencia,)).fetchone() is not None:
                error = 'Esta referencia ya existe'.format(referencia)
                flash(error)
                return render_template('registrar_producto.html')

            db.execute(
                'INSERT INTO accesorio (referencia, nombre, cantidad, imagen, estado, tipo_accesorio) VALUES (?,?,?,?,?,?)',
                (referencia, nombre, cantidad, filename, state, tipo)
            )

            mensaje = "Se creó el producto "+nombre

            now = datetime.now()  # current date and time

            fechaActual = now.strftime("%m/%d/%Y, %H:%M:%S")

            db.execute(
                'INSERT INTO movimiento (idUser, referenciaAccesorio, dateMovement, descripcion) VALUES (?,?,?,?)',
                (session['idUser'], referencia, fechaActual, mensaje)
            )
            db.commit()
            flash('Producto Registrado con exito')
            return render_template('administrador.html')

        return render_template('administrador.html')
    except:
        print('nada')
        return render_template('iniciar_sesion.html')


#Cambiar clave Template
@app.route('/cambiarclaveview/<usr>', methods=('GET', 'POST'))
def cambiarclaveview(usr):

    session['user'] = usr
    return render_template('cambiar_contraseña.html')


# Backend de Cambiar clave
@app.route('/cambiarclave', methods=('GET', 'POST'))
def cambiarclave():
    try:
        if request.method == 'POST':
            db = get_db()
            error = None

            password = request.form['password']
            print(password)
            confirm_password = request.form['confirmar_password']
            print(confirm_password)
            username = session['user']
            clave = werkzeug.security.generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

            if not utils.isPasswordValid(password):
                flash("La contraseña debe contener al menos una minúscula, una mayúscula, un número y 8 caracteres")
                return render_template('cambiar_contraseña.html')
            if password != confirm_password:
                flash("Las contraseñas no coinciden, intentelo nuevamente")
                return render_template('cambiar_contraseña.html')


            db.execute('UPDATE usuarios SET contraseña = ? WHERE usuario = ?', (clave, username,)).fetchone()
            db.commit()
            flash("La contraseña ha sido cambiado exitosamente")

        return render_template('iniciar_sesion.html')

    except:
        print('nada')

    return render_template('cambiar_contraseña.html')


#Backend de Cambiar Clave para enviar correo y TEMPLATE
@app.route('/validarusuario', methods=('GET', 'POST'))
def validarusuario():
    try:
        if request.method == 'POST':
            db = get_db()
            error = None
            username = request.form['usuario_registrado']
            email = request.form['correo']
            user = db.execute('SELECT * FROM usuarios WHERE usuario = ?', (username,)).fetchone()
            session['username'] = request.form['usuario_registrado']
            if user is None:
                flash("Usuario inválido")
                flash("Usuario inválido")
                return render_template('iniciar_sesion.html')
            else:
                mensaje = "<html>" \
                          "<head><center><title>REESTABLECER CONTRASEÑA</title></center></head>" \
                          "<body style='background: #DCDCDC;>" \
                          "<center><h1 style='font-weight: bold;' ></h1></center>" \
                          "<center><div style='width:450px; background: white; border-radius:5px;'>" \
                          "<img src='https://i.ibb.co/x8ns2tq/HANDMADE.png' style='width:450px; height:100px'><br><br>" \
                          "Cordial Saludo <br><br>" \
                          "Hemos recibido tu solicitud para cambiar de contraseña<br><br>" \
                          "Usuario: <strong>" +username+ "</strong> <br><br>"+  \
                          "Para acceder al sistema, reestablece tu contraseña a través de el siguiente enlace: <a href='https://54.227.121.118/cambiarclaveview/"+username+"' style='font-weight: bold;'> INGRESAR </a><br><br>" \
                                                                                              "<div style='background-color:rgb(235,99,107);  height:20px; width: 450px;'></div>" \
                                                                                              "</div></center>" \
                                                                                              "</body>" \
                                                                                              "</html>"
                flash("Ingresa a tu correo y accede al link para cambiar de contraseña")
                yag = yagmail.SMTP('handmadeJewellery20202@gmail.com', 'handmade2020')
                yag.send(to=email, subject='Confirmación de Registro', contents=mensaje)

                return redirect(url_for("login"))
                #return render_template('cambiar_contraseña.html')

        return render_template('validar_usuario.html')
    except:
        print('Usuario except')
        return render_template('iniciar_sesion.html')


# Registrar Usuario - Administrador - TEMPLATE
@app.route('/administrador/registrar_usuario')
def registrar_usuario():
    try:
        if session['rol'] == 1:
            return render_template('registrar_usuario.html')
        elif session['rol'] == 0:
            return redirect(url_for("inicio_usuario"))
    except:
        return redirect(url_for("logout"))


#Backend de registro del usuario
@app.route('/administrador/registro', methods=('GET', 'POST'))
def registro():
    if request.method == 'POST':
        db = get_db()
        error = None
        name = request.form['name']
        usuario = request.form['usuario']
        correo = request.form['correo']
        password = request.form['password']
        clave = werkzeug.security.generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
        casilla = False
        try:
            casillaResult = request.form['casilla_administrador']
            if casillaResult == "on":
                casilla = True
        except:
            print("paso")

        try:
            db.execute(
                'INSERT INTO usuarios (nombre, usuario, correo, contraseña, administrador) VALUES (?,?,?,?,?)', (name, usuario, correo, clave, casilla)
            )
            db.commit()
            mensaje = "<html>" \
                      "<head><center><title>SOLICITUD PARA REGISTRO DE USUARIO</title></center></head>" \
                      "<body style='background: #DCDCDC;>" \
                      "<center><h1 style='font-weight: bold;' ></h1></center>" \
                      "<center><div style='width:450px; background: white; border-radius:5px;'>" \
                      "<img src='https://i.ibb.co/x8ns2tq/HANDMADE.png' style='width:450px; height:100px'><br><br>" \
                      "Cordial Saludo <br><br>" \
                      "Se ha activado su cuenta, a partir de ahora puedes ingresar a la tienda de Accesorios HANDMADE<br><br>" \
                      "Los datos de ingreso son:<br><br>" \
                      "Usuario: <strong>" + usuario + "</strong><br>" \
                      "Contraseña: <strong>" + password + "</strong><br><br>" \
                      "Para acceder al sistema, lo podra hacer mediante el siguiente enlace: <a href='https://54.227.121.118' style='font-weight: bold;'> INGRESAR </a><br><br>" \
                      "<div style='background-color:rgb(235,99,107);  height:20px; width: 450px;'></div>" \
                      "</div></center>" \
                      "</body>" \
                      "</html>"

            yag = yagmail.SMTP('handmadeJewellery20202@gmail.com', 'handmade2020')
            yag.send(to=correo, subject='Confirmación de Registro', contents=mensaje)
            flash("Usuario Registrado con Éxito")
            return redirect(url_for("administrador.html"))
        except:
            flash("Error al registro, verifique nuevamente")
            return render_template('administrador.html')


#Ruta 1: Inicio como administrador: Permite visualizar, crear y modificar todos los accesorios y usuarios

@app.route('/administrador')
def inicio_administrador():
    try:
        if session['rol'] == 1:
            return render_template("administrador.html")
        elif session['rol'] == 0:
            return redirect(url_for("inicio_usuario"))
    except:
        return redirect(url_for("logout"))


@app.route('/administrador/agregar_accesorio')
def agregar_accesorio():
    try:
        if session['rol'] == 1:
            return render_template("registrar_producto.html")
        elif session['rol'] == 0:
            return redirect(url_for("inicio_usuario"))
    except:
        return redirect(url_for("logout"))


@app.route('/administrador/ver_inventario')
def ver_inventario():
    try:
        if session['rol'] == 1:
            return render_template("ver_inventario.html")
        elif session['rol'] == 0:
            return redirect(url_for("inicio_usuario"))
    except:
        return redirect(url_for("logout"))


@app.route('/administrador/ver_usuarios')
def ver_usuarios():
    try:
        if session['rol'] == 1:
            return render_template("ver_usuarios.html")
        elif session['rol'] == 0:
            return redirect(url_for("inicio_usuario"))
    except:
        return redirect(url_for("logout"))


#Template editar-Eliminar Producto Administrador
@app.route('/administrador/producto_administrador/<id>')
def producto_administrador(id):
    try:
        if session['rol'] == 1:
            db = get_db()
            print(id)
            inventario = db.execute('SELECT * FROM accesorio WHERE id = ? AND estado = ?', (id, "Activo")).fetchone()
            print("paso2")
            if inventario is None:
                print("paso3")
                flash("Este Producto ha sido Eliminado")
                return redirect(url_for("inicio_administrador"))
            else:
                return render_template("producto_administrador.html", inventario=inventario)
        elif session['rol'] == 0:
            return redirect(url_for("inicio_usuario"))
    except:
        return redirect(url_for("logout"))


#Backend editar Producto Admin
@app.route('/administrador/modificar_producto', methods=('GET', 'POST'))
def editarProductoAdministrador():
    try:
        if request.method == 'POST':

            db = get_db()
            error = None
            nombre = request.form['nombre']
            referencia = request.form['referencia']
            cantidad = request.form['cantidad']
            idAccesorio = request.form['id']
            accesorio = db.execute('UPDATE accesorio SET nombre = ?, cantidad = ?, referencia = ? WHERE id = ?', (nombre, cantidad, referencia, idAccesorio)).fetchone()

            mensaje = "Se Edito el producto " + nombre + " con referencia: "+referencia

            now = datetime.now()  # current date and time

            fechaActual = now.strftime("%m/%d/%Y, %H:%M:%S")

            db.execute(
                'INSERT INTO movimiento (idUser, referenciaAccesorio, dateMovement, descripcion) VALUES (?,?,?,?)',
                (session['idUser'], referencia, fechaActual, mensaje)
            )
            db.commit()

            flash("Producto "+nombre+" Editado Correctamente")
            return redirect(url_for("inicio_administrador"))
        return render_template('formulario_registro.html')
    except:
        flash("No se pudo editar el Producto " + nombre + ", Intentelo Nuevamente")
        return redirect(url_for("inicio_administrador"))


#Backend Eliminar Producto Admin
@app.route('/administrador/eliminar_producto/<id>/<ref>', methods=('GET', 'POST'))
def eliminarProducto(id, ref):
    try:

        db = get_db()
        error = None
        accesorio = db.execute('UPDATE accesorio SET estado = ? WHERE id = ?', ("Inactivo", id)).fetchone()

        mensaje = "Se Elimino el producto con referencia "+ref+" exitosamente"

        now = datetime.now()  # current date and time

        fechaActual = now.strftime("%m/%d/%Y, %H:%M:%S")

        db.execute(
            'INSERT INTO movimiento (idUser, referenciaAccesorio, dateMovement, descripcion) VALUES (?,?,?,?)',
            (session['idUser'], ref, fechaActual, mensaje)
        )
        db.commit()

        flash("Producto Eliminado Correctamente")

        return redirect(url_for("inicio_administrador"))
    except:
        flash("No se pudo eliminar el Producto , Intentelo Nuevamente")
        return redirect(url_for("inicio_administrador"))


@app.route('/administrador/aretes')
def aretes():
    try:
        if session['rol'] == 1:
            db = get_db()
            tipo = 'Aretes'
            accesorioto = db.execute('SELECT * FROM accesorio WHERE tipo_accesorio = ? AND estado = ?', (tipo, "Activo")).fetchall()
            return render_template("aretes.html", accesorioto=accesorioto)
        elif session['rol'] == 0:
            return redirect(url_for("inicio_usuario"))
    except:
        return redirect(url_for("logout"))


@app.route('/administrador/anillos')
def anillos():
    try:
        if session['rol'] == 1:
            db = get_db()
            tipo = 'Anillos'
            accesorioto = db.execute('SELECT * FROM accesorio WHERE tipo_accesorio = ? AND estado = ?', (tipo, "Activo")).fetchall()
            return render_template("anillos.html", accesorioto=accesorioto)
        elif session['rol'] == 0:
            return redirect(url_for("inicio_usuario"))
    except:
        return redirect(url_for("logout"))


@app.route('/administrador/collares')
def collares():
    try:
        if session['rol'] == 1:
            db = get_db()
            tipo = 'Collares'
            accesorioto = db.execute('SELECT * FROM accesorio WHERE tipo_accesorio = ? AND estado = ?', (tipo, "Activo")).fetchall()
            return render_template("collares.html", accesorioto=accesorioto)
        elif session['rol'] == 0:
            return redirect(url_for("inicio_usuario"))
    except:
        return redirect(url_for("logout"))


@app.route('/administrador/pulseras')
def pulseras():
    try:
        if session['rol'] == 1:
            db = get_db()
            tipo = 'Pulseras'
            accesorioto = db.execute('SELECT * FROM accesorio WHERE tipo_accesorio = ? AND estado = ?', (tipo, "Activo")).fetchall()
            return render_template("pulseras.html", accesorioto=accesorioto)
        elif session['rol'] == 0:
            return redirect(url_for("inicio_usuario"))
    except:
        return redirect(url_for("logout"))


@app.route('/administrador/inventario')
def inventarioAdministrador():
    try:
        if session['rol'] == 1:
            db = get_db()
            accesorioto = db.execute('SELECT * FROM accesorio WHERE estado = ?', ("Activo",)).fetchall()
            return render_template("ver_inventario.html", accesorioto=accesorioto)
        elif session['rol'] == 0:
            return redirect(url_for("inicio_usuario"))
    except:
        return redirect(url_for("logout"))


@app.route('/administrador/usuarios')
def usuariosAdministador():
    try:
        if session['rol'] == 1:
            db = get_db()
            accesorioto = db.execute('SELECT * FROM usuarios').fetchall()
            return render_template("ver_usuarios.html", usuario=accesorioto)
        elif session['rol'] == 0:
            return redirect(url_for("inicio_usuario"))
    except:
        return redirect(url_for("logout"))


@app.route('/modificar_usuario')
def usuario():
    return render_template("modificar_usuario.html")


#Ruta 2: Inicio como usuario: Permite visualizar y modificar cantidad de productos
@app.route('/usuario')
def inicio_usuario():
    try:
        if session['rol'] == 0:
            return render_template("inicio.html")
    except:
        return redirect(url_for("logout"))


@app.route('/usuario/ver_aretes')
def ver_aretes():
    try:
        if session['rol'] == 0:
            db = get_db()
            tipo = 'Aretes'
            accesorioto = db.execute('SELECT * FROM accesorio WHERE tipo_accesorio = ? AND estado = ?', (tipo, "Activo")).fetchall()
            return render_template("ver_aretes.html", accesorioto=accesorioto)
        elif session['rol'] == 1:
            return redirect(url_for("inicio_administrador"))
    except:
        return redirect(url_for("logout"))


@app.route('/usuario/ver_collares')
def ver_collares():
    try:
        if session['rol'] == 0:
            db = get_db()
            tipo = 'Collares'
            accesorioto = db.execute('SELECT * FROM accesorio WHERE tipo_accesorio = ? AND estado = ?', (tipo, "Activo")).fetchall()
            return render_template("ver_collares.html", accesorioto=accesorioto)
        elif session['rol'] == 1:
            return redirect(url_for("inicio_administrador"))
    except:
        return redirect(url_for("logout"))


@app.route('/usuario/ver_pulseras')
def ver_pulseras():
    try:
        if session['rol'] == 0:
            db = get_db()
            tipo = 'Pulseras'
            accesorioto = db.execute('SELECT * FROM accesorio WHERE tipo_accesorio = ? AND estado = ?', (tipo, "Activo")).fetchall()
            return render_template("ver_pulseras.html", accesorioto=accesorioto)
        elif session['rol'] == 1:
            return redirect(url_for("inicio_administrador"))
    except:
        return redirect(url_for("logout"))


@app.route('/usuario/ver_anillos')
def ver_anillos():
    try:
        if session['rol'] == 0:
            db = get_db()
            tipo = 'Anillos'
            accesorioto = db.execute('SELECT * FROM accesorio WHERE tipo_accesorio = ? AND estado = ?', (tipo, "Activo")).fetchall()
            return render_template("ver_anillos.html", accesorioto=accesorioto)
        elif session['rol'] == 1:
            return redirect(url_for("inicio_administrador"))
    except:
        return redirect(url_for("logout"))


@app.route('/usuario/ver_producto/<id>', methods=('GET', 'POST'))
def ver_producto(id):
    try:
        if session['rol'] == 0:
            db = get_db()
            inventario = db.execute('SELECT * FROM accesorio WHERE id = ? AND estado = ?', (id, "Activo")).fetchone()
            if inventario is None:
                flash("Este Producto ha sido Eliminado")
                return redirect(url_for("inicio_usuario"))
            else:
                return render_template("ver_producto.html", inventario=inventario)
        elif session['rol'] == 1:
            return redirect(url_for("inicio_administrador"))
    except:
        return redirect(url_for("logout"))


#Editar Producto Usuario
#Backend editar Producto Admin
@app.route('/usuario/modificar_producto', methods=('GET', 'POST'))
def editarProductoUsuario():
    try:
        if request.method == 'POST':

            db = get_db()
            error = None
            nombre = request.form['nombre']
            referencia = request.form['referencia']
            cantidad = request.form['cantidad']
            idAccesorio = request.form['id']
            accesorio = db.execute('UPDATE accesorio SET nombre = ?, cantidad = ?, referencia = ? WHERE id = ?', (nombre, cantidad, referencia, idAccesorio)).fetchone()

            mensaje = "Se Edito el producto " + nombre + " con referencia: "+referencia

            now = datetime.now()  # current date and time

            fechaActual = now.strftime("%m/%d/%Y, %H:%M:%S")

            db.execute(
                'INSERT INTO movimiento (idUser, referenciaAccesorio, dateMovement, descripcion) VALUES (?,?,?,?)',
                (session['idUser'], referencia, fechaActual, mensaje)
            )
            db.commit()

            flash("Producto "+nombre+" Editado Correctamente")
            return redirect(url_for("inicio_usuario"))
        return render_template('formulario_registro.html')
    except:
        flash("No se pudo editar el Producto " + nombre + ", Intentelo Nuevamente")
        return redirect(url_for("inicio_usuario"))


#Botón de búsqueda
@app.route('/administrador/buscar', methods=('GET', 'POST'))
def buscar_admin():
    try:
        if request.method == 'POST':
            db = get_db()
            buscar = request.form['search']
            palabra = "%" + buscar + "%"
            accesorioto = db.execute('SELECT * FROM accesorio WHERE nombre LIKE ? ', (palabra,)).fetchall()
            if accesorioto is None:
                return redirect(url_for("inicio_administrador"))
            else:
                return render_template("ver_inventario.html", accesorioto=accesorioto)
    except:
        return redirect(url_for("logout"))


@app.route('/usuario/buscar', methods=('GET', 'POST'))
def buscar_user():
    try:
        if request.method == 'POST':
            db = get_db()
            buscar = request.form['search']
            palabra = "%" + buscar + "%"
            accesorioto = db.execute('SELECT * FROM accesorio WHERE nombre LIKE ? ', (palabra,)).fetchall()
            if accesorioto is None:
                return redirect(url_for("inicio_usuario"))
            else:
                return render_template("ver_busqueda.html", accesorioto=accesorioto)
    except:
        return redirect(url_for("logout"))


if __name__ == '__main__':
    app.run( debug=True, host='0.0.0.0', port=443, ssl_context='adhoc' )
