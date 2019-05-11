from flask import Flask


app = Flask(__name__)
app.config.from_pyfile('app.cfg')


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/', methods=['GET', 'POST'])
def test_launcher():
    from flask import render_template, request, flash, redirect
    from tc_manager import execute_tests
    input_field_name = 'testInput'
    if request.method == 'POST':
        # check if the post request has the file part
        if input_field_name not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files[input_field_name]
        # if user does not select file, browser also submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            execute_tests(file)
            return render_template("testMonitor.html")
    return render_template("test_launcher.html")


@app.errorhandler(404)
def page_not_found(error):
    from flask import render_template
    return render_template('error404.html', error=error), 404


@app.errorhandler(500)
def page_not_found(error):
    from flask import render_template
    return render_template('error500.html', error=error), 500


if __name__ == '__main__':
    app.run()
