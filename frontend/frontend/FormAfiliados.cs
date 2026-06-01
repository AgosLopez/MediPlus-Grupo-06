using System.Diagnostics;
using System.Text;
using System.Text.Json;

namespace frontend
{
    public partial class FormAfiliados : Form
    {
        private readonly string _pythonExe;
        private readonly string _scriptPath;
        private List<JsonElement> _afiliados = new();

        public FormAfiliados()
        {
            InitializeComponent();

            // Ajustá esta ruta si es necesario
            string backend = @"C:\3ro\Ing de Datos 2\MediPlus-Grupo-06\backend";
            _pythonExe = Path.Combine(backend, @"venv\Scripts\python.exe");
            _scriptPath = Path.Combine(backend, @"queries\afiliados_query.py");

            btnCargar.Click += BtnCargar_Click;
            listAfiliados.SelectedIndexChanged += ListAfiliados_SelectedIndexChanged;
        }

        private string EjecutarPython(params string[] args)
        {
            var psi = new ProcessStartInfo
            {
                FileName = _pythonExe,
                Arguments = $"\"{_scriptPath}\" {string.Join(" ", args)}",
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true,
                StandardOutputEncoding = Encoding.UTF8,
            };

            using var proc = Process.Start(psi)!;
            string stdout = proc.StandardOutput.ReadToEnd();
            string stderr = proc.StandardError.ReadToEnd();
            proc.WaitForExit();

            if (!string.IsNullOrWhiteSpace(stderr))
                MessageBox.Show($"Error Python:\n{stderr}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);

            return stdout;
        }

        private void BtnCargar_Click(object sender, EventArgs e)
        {
            listAfiliados.Items.Clear();
            txtDetalle.Clear();
            _afiliados.Clear();
            btnCargar.Enabled = false;
            btnCargar.Text = "Cargando...";

            try
            {
                string json = EjecutarPython("listar");
                var lista = JsonSerializer.Deserialize<List<JsonElement>>(json);
                if (lista == null) return;

                foreach (var a in lista)
                {
                    string id = a.GetProperty("_id").GetString() ?? "";
                    string nombre = a.TryGetProperty("nombre", out var n) ? n.GetString() ?? "" : "";
                    string apellido = a.TryGetProperty("apellido", out var ap) ? ap.GetString() ?? "" : "";
                    listAfiliados.Items.Add($"{id} — {apellido}, {nombre}");
                    _afiliados.Add(a);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error:\n{ex.Message}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            finally
            {
                btnCargar.Enabled = true;
                btnCargar.Text = "Cargar Afiliados";
            }
        }

        private void ListAfiliados_SelectedIndexChanged(object sender, EventArgs e)
        {
            int idx = listAfiliados.SelectedIndex;
            if (idx < 0) return;

            string id = _afiliados[idx].GetProperty("_id").GetString() ?? "";

            try
            {
                string json = EjecutarPython("detalle", id);
                var doc = JsonSerializer.Deserialize<JsonElement>(json);
                txtDetalle.Text = FormatearAfiliado(doc);
            }
            catch (Exception ex)
            {
                txtDetalle.Text = $"Error: {ex.Message}";
            }
        }

        private static string FormatearAfiliado(JsonElement doc)
        {
            var sb = new StringBuilder();

            void Linea(string etiqueta, string valor) =>
                sb.AppendLine($"{etiqueta,-28}{valor}");

            void Titulo(string texto)
            {
                sb.AppendLine();
                sb.AppendLine($"?? {texto} " + new string('?', Math.Max(0, 40 - texto.Length)));
            }

            string Str(string campo) =>
                doc.TryGetProperty(campo, out var v) && v.ValueKind != JsonValueKind.Null
                    ? v.GetString() ?? "—" : "—";

            Titulo("IDENTIFICACIÓN");
            Linea("ID:", Str("_id"));
            Linea("Nro. Afiliado:", Str("numero_afiliado"));
            Linea("DNI:", Str("dni"));
            Linea("Estado:", Str("estado"));

            Titulo("DATOS PERSONALES");
            Linea("Nombre:", $"{Str("nombre")} {Str("apellido")}");
            Linea("Fecha nac.:", Str("fecha_nacimiento"));
            Linea("Género:", Str("genero"));
            Linea("Grupo sanguíneo:", Str("grupo_sanguineo"));
            Linea("Email:", Str("email"));
            Linea("Teléfono:", Str("telefono"));

            if (doc.TryGetProperty("direccion", out var dir))
            {
                Titulo("DIRECCIÓN");
                string D(string c) => dir.TryGetProperty(c, out var v) ? v.GetString() ?? "" : "";
                Linea("Calle:", $"{D("calle")} {D("numero")}");
                Linea("Ciudad:", D("ciudad"));
                Linea("Provincia:", D("provincia"));
                Linea("CP:", D("codigo_postal"));
                Linea("Zona:", D("zona"));
            }

            if (doc.TryGetProperty("plan_salud", out var plan))
            {
                Titulo("PLAN DE SALUD");
                string P(string c) => plan.TryGetProperty(c, out var v) ? v.GetString() ?? "" : "";
                Linea("Código:", P("codigo_plan"));
                Linea("Nombre:", P("nombre"));
                Linea("Cuota mensual:", plan.TryGetProperty("cuota_mensual", out var cm) ? $"${cm.GetDecimal():N0}" : "—");
                Linea("Cob. medicamentos:", plan.TryGetProperty("cobertura_medicamentos", out var cmed) ? $"{cmed.GetInt32()}%" : "—");
                Linea("Cob. estudios:", plan.TryGetProperty("cobertura_estudios", out var ces) ? $"{ces.GetInt32()}%" : "—");
                Linea("Copago consulta:", plan.TryGetProperty("copago_consulta", out var cop) ? $"${cop.GetDecimal():N0}" : "—");
            }

            Titulo("GRUPO FAMILIAR");
            Linea("Grupo ID:", Str("grupo_familiar_id"));
            Linea("Rol:", Str("rol_familiar"));
            Linea("Médico cabecera:", Str("medico_cabecera_id"));
            Linea("Fecha alta:", Str("fecha_alta"));

            if (doc.TryGetProperty("enfermedades", out var enf) && enf.GetArrayLength() > 0)
            {
                Titulo("ENFERMEDADES");
                foreach (var e in enf.EnumerateArray())
                {
                    string E(string c) => e.TryGetProperty(c, out var v) && v.ValueKind != JsonValueKind.Null ? v.GetString() ?? "—" : "—";
                    sb.AppendLine($"  • {E("nombre")} ({E("tipo")}) — CIE10: {E("cie10")}");
                    sb.AppendLine($"    Diagnóstico: {E("fecha_diagnostico")}  |  Severidad: {E("severidad")}");
                    if (E("notas") != "—")
                        sb.AppendLine($"    Notas: {E("notas")}");
                }
            }

            return sb.ToString();
        }
    }
}