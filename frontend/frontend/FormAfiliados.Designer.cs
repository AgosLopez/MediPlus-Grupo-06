namespace frontend
{
    partial class FormAfiliados
    {
        /// <summary>
        ///  Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        ///  Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        /// <summary>
        ///  Required method for Designer support - do not modify
        ///  the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            splitContainer1 = new SplitContainer();
            btnCargar = new Button();
            listAfiliados = new ListBox();
            txtDetalle = new RichTextBox();
            ((System.ComponentModel.ISupportInitialize)splitContainer1).BeginInit();
            splitContainer1.Panel1.SuspendLayout();
            splitContainer1.Panel2.SuspendLayout();
            splitContainer1.SuspendLayout();
            SuspendLayout();
            // 
            // splitContainer1
            // 
            splitContainer1.Dock = DockStyle.Fill;
            splitContainer1.Location = new Point(0, 0);
            splitContainer1.Name = "splitContainer1";
            // 
            // splitContainer1.Panel1
            // 
            splitContainer1.Panel1.Controls.Add(listAfiliados);
            splitContainer1.Panel1.Controls.Add(btnCargar);
            // 
            // splitContainer1.Panel2
            // 
            splitContainer1.Panel2.Controls.Add(txtDetalle);
            splitContainer1.Size = new Size(800, 450);
            splitContainer1.SplitterDistance = 266;
            splitContainer1.TabIndex = 0;
            // 
            // btnCargar
            // 
            btnCargar.Dock = DockStyle.Top;
            btnCargar.Location = new Point(0, 0);
            btnCargar.Name = "btnCargar";
            btnCargar.Size = new Size(266, 35);
            btnCargar.TabIndex = 0;
            btnCargar.Text = "Cargar Afiliados";
            btnCargar.UseVisualStyleBackColor = true;
            // 
            // listAfiliados
            // 
            listAfiliados.Dock = DockStyle.Fill;
            listAfiliados.FormattingEnabled = true;
            listAfiliados.Location = new Point(0, 35);
            listAfiliados.Name = "listAfiliados";
            listAfiliados.Size = new Size(266, 415);
            listAfiliados.TabIndex = 1;
            // 
            // txtDetalle
            // 
            txtDetalle.Dock = DockStyle.Fill;
            txtDetalle.Location = new Point(0, 0);
            txtDetalle.Name = "txtDetalle";
            txtDetalle.ReadOnly = true;
            txtDetalle.Size = new Size(530, 450);
            txtDetalle.TabIndex = 0;
            txtDetalle.Text = "";
            // 
            // FormAfiliados
            // 
            AutoScaleDimensions = new SizeF(8F, 20F);
            AutoScaleMode = AutoScaleMode.Font;
            ClientSize = new Size(800, 450);
            Controls.Add(splitContainer1);
            Name = "FormAfiliados";
            Text = "Form1";
            splitContainer1.Panel1.ResumeLayout(false);
            splitContainer1.Panel2.ResumeLayout(false);
            ((System.ComponentModel.ISupportInitialize)splitContainer1).EndInit();
            splitContainer1.ResumeLayout(false);
            ResumeLayout(false);
        }

        #endregion

        private SplitContainer splitContainer1;
        private Button btnCargar;
        private ListBox listAfiliados;
        private RichTextBox txtDetalle;
    }
}
