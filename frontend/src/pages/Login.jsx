import { Link } from "react-router-dom";
import InputField from "../components/ui/InputField";
import SubmitButton from "../components/ui/SubmitButton";
import { FaUserCircle } from "react-icons/fa";
function Login(){
    return(
        <main className="flex justify-center items-center h-screen bg-gray-100">
            <section 
                className="bg-white p-8 rounded-lg shadow-md 
                        w-11/12 sm:w-10/12 md:w-8/12 lg:w-6/12
                        h-10/12 flex flex-col items-center"
            >
                <FaUserCircle className="text-6xl mb-2"/>
                <h1 className="text-xl font-bold">Iniciar Sesión</h1>
                <form action="" className="mt-4 flex flex-col gap-10 justify-center items-center w-9/12">
                    <InputField label="Correo Electrónico" type="text" name="email" placeholder="example@mail.com"/>
                    <InputField label="Contraseña" type="password" name="password"/>
                    <SubmitButton text="Iniciar Sesión" className="w-4/5 mt-5 bg-blue-500 hover:bg-blue-600"/>
                    <p className="mt-4 text-sm text-gray-600">
                    ¿No tienes una cuenta? 
                    <Link to="/register" className="text-blue-500 hover:underline ml-1">
                        Regístrate aquí
                    </Link>
                </p>
                </form>
            </section> 
        </main>
    );
}
export default Login;