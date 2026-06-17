<template>
  <div class="image-upload-container">
    <div class="upload-section">
      <!-- Input de archivo oculto -->
      <input
        ref="fileInput"
        type="file"
        accept="image/jpeg,image/png,image/gif,image/webp"
        @change="handleFileSelect"
        style="display: none"
      />

      <!-- Botón para seleccionar archivo -->
      <button
        @click="$refs.fileInput.click()"
        class="btn-select-image"
        :disabled="uploading"
      >
        <span v-if="!uploading">📷 Seleccionar Imagen</span>
        <span v-else>Cargando...</span>
      </button>

      <!-- Vista previa de la imagen -->
      <div v-if="preview" class="preview-container">
        <img :src="preview" alt="Preview" class="image-preview" />
        <p class="file-name">{{ selectedFileName }}</p>
        <button
          @click="uploadImage"
          class="btn-upload"
          :disabled="uploading"
        >
          {{ uploading ? "Subiendo..." : "Subir a Firebase" }}
        </button>
        <button
          @click="clearPreview"
          class="btn-cancel"
          :disabled="uploading"
        >
          Cancelar
        </button>
      </div>

      <!-- Mensaje de estado -->
      <div v-if="message" :class="['message', messageType]">
        {{ message }}
      </div>

      <!-- URL de la imagen subida -->
      <div v-if="uploadedImageUrl" class="uploaded-url">
        <p>✅ Imagen subida exitosamente</p>
        <input
          type="text"
          :value="uploadedImageUrl"
          readonly
          class="url-input"
        />
        <button @click="copyToClipboard" class="btn-copy">
          📋 Copiar URL
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "ImageUploader",
  props: {
    folder: {
      type: String,
      default: "images"
    },
    uploadEndpoint: {
      type: String,
      default: "/upload-image"
    },
    playerId: {
      type: Number,
      default: null
    },
    teamId: {
      type: Number,
      default: null
    }
  },
  emits: ["upload-success", "upload-error"],
  data() {
    return {
      selectedFile: null,
      selectedFileName: "",
      preview: null,
      uploading: false,
      message: "",
      messageType: "info",
      uploadedImageUrl: null
    };
  },
  methods: {
    handleFileSelect(event) {
      const file = event.target.files[0];
      if (!file) return;

      // Validar tipo de archivo
      const validTypes = ["image/jpeg", "image/png", "image/gif", "image/webp"];
      if (!validTypes.includes(file.type)) {
        this.showMessage("❌ Por favor selecciona una imagen válida (JPG, PNG, GIF, WebP)", "error");
        return;
      }

      // Validar tamaño (máximo 5MB)
      const maxSize = 5 * 1024 * 1024;
      if (file.size > maxSize) {
        this.showMessage("❌ El archivo es demasiado grande. Máximo: 5MB", "error");
        return;
      }

      this.selectedFile = file;
      this.selectedFileName = file.name;

      // Crear vista previa
      const reader = new FileReader();
      reader.onload = (e) => {
        this.preview = e.target.result;
      };
      reader.readAsDataURL(file);
    },

    async uploadImage() {
      if (!this.selectedFile) {
        this.showMessage("❌ No hay archivo seleccionado", "error");
        return;
      }

      this.uploading = true;
      this.message = "";

      try {
        const formData = new FormData();
        formData.append("file", this.selectedFile);
        formData.append("folder", this.folder);

        // Si es una foto de jugador o logo de equipo, usar endpoint especializado
        let endpoint = this.uploadEndpoint;
        if (this.playerId && this.uploadEndpoint === "/upload-image") {
          endpoint = "/upload-player-photo";
          formData.append("player_id", this.playerId);
        } else if (this.teamId && this.uploadEndpoint === "/upload-image") {
          endpoint = "/upload-team-logo";
          formData.append("team_id", this.teamId);
        }

        // Obtener la URL base del servidor (usando import.meta.env en Vite)
        const serverUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";

        const response = await fetch(`${serverUrl}${endpoint}`, {
          method: "POST",
          body: formData
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || "Error al subir imagen");
        }

        const data = await response.json();
        this.uploadedImageUrl = data.url;

        this.showMessage("✅ Imagen subida exitosamente", "success");
        this.$emit("upload-success", {
          url: data.url,
          filename: data.filename,
          playerId: this.playerId,
          teamId: this.teamId
        });

        // Limpiar después de 3 segundos
        setTimeout(() => {
          this.clearPreview();
        }, 3000);

      } catch (error) {
        console.error("Error uploading image:", error);
        this.showMessage(`❌ ${error.message}`, "error");
        this.$emit("upload-error", error);
      } finally {
        this.uploading = false;
      }
    },

    clearPreview() {
      this.selectedFile = null;
      this.selectedFileName = "";
      this.preview = null;
      this.uploadedImageUrl = null;
      this.message = "";
      this.$refs.fileInput.value = "";
    },

    showMessage(text, type = "info") {
      this.message = text;
      this.messageType = type;

      if (type === "success") {
        setTimeout(() => {
          this.message = "";
        }, 5000);
      }
    },

    copyToClipboard() {
      if (this.uploadedImageUrl) {
        navigator.clipboard.writeText(this.uploadedImageUrl);
        this.showMessage("📋 URL copiada al portapapeles", "success");
      }
    }
  }
};
</script>

<style scoped>
.image-upload-container {
  max-width: 500px;
  margin: 20px auto;
  padding: 20px;
  background: #f9f9f9;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.upload-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.btn-select-image,
.btn-upload,
.btn-cancel,
.btn-copy {
  padding: 10px 16px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-select-image {
  background-color: #007bff;
  color: white;
  border: 2px solid #007bff;
}

.btn-select-image:hover:not(:disabled) {
  background-color: #0056b3;
  border-color: #0056b3;
}

.btn-select-image:disabled {
  background-color: #ccc;
  border-color: #ccc;
  cursor: not-allowed;
}

.btn-upload {
  background-color: #28a745;
  color: white;
  border: 2px solid #28a745;
}

.btn-upload:hover:not(:disabled) {
  background-color: #218838;
  border-color: #218838;
}

.btn-upload:disabled {
  background-color: #ccc;
  border-color: #ccc;
  cursor: not-allowed;
}

.btn-cancel {
  background-color: #dc3545;
  color: white;
  border: 2px solid #dc3545;
}

.btn-cancel:hover:not(:disabled) {
  background-color: #c82333;
  border-color: #c82333;
}

.btn-cancel:disabled {
  background-color: #ccc;
  border-color: #ccc;
  cursor: not-allowed;
}

.btn-copy {
  background-color: #6c757d;
  color: white;
  border: 2px solid #6c757d;
}

.btn-copy:hover {
  background-color: #5a6268;
  border-color: #5a6268;
}

.preview-container {
  text-align: center;
  padding: 16px;
  background: white;
  border-radius: 6px;
  border: 2px dashed #007bff;
}

.image-preview {
  max-width: 100%;
  max-height: 300px;
  border-radius: 6px;
  margin: 16px 0;
  object-fit: cover;
}

.file-name {
  color: #666;
  font-size: 12px;
  margin: 8px 0;
  word-break: break-word;
}

.message {
  padding: 12px 16px;
  border-radius: 6px;
  font-size: 14px;
  text-align: center;
  font-weight: 500;
}

.message.success {
  background-color: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.message.error {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.message.info {
  background-color: #d1ecf1;
  color: #0c5460;
  border: 1px solid #bee5eb;
}

.uploaded-url {
  padding: 16px;
  background: white;
  border-radius: 6px;
  border-left: 4px solid #28a745;
}

.uploaded-url p {
  color: #28a745;
  font-weight: 600;
  margin: 0 0 8px 0;
}

.url-input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 12px;
  font-family: monospace;
  background-color: #f5f5f5;
  margin-bottom: 8px;
}

.url-input:focus {
  outline: none;
  border-color: #007bff;
  background-color: #fff;
}
</style>
