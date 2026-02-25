#!/usr/bin/env bash

# =========================
# Diretório de destino
# =========================
DEST_DIR="$HOME/Documentos/GitHub/tflite/modelos"
CC_DIR="$DEST_DIR/cc"
H_DIR="$DEST_DIR/h"

mkdir -p "$CC_DIR" "$H_DIR"

# =========================
# Converter todos os .tflite do diretório atual
# =========================
for MODEL in *.tflite; do
    if [ ! -f "$MODEL" ]; then
        echo "❌ Nenhum arquivo .tflite encontrado neste diretório"
        exit 1
    fi

    BASENAME="${MODEL%.tflite}"
    SYMBOL="${BASENAME}_tflite"

    CC_FILE="$CC_DIR/${BASENAME}_model.cc"
    H_FILE="$H_DIR/${BASENAME}_model.h"
    HEADER_NAME="${BASENAME}_model.h"

    # Guard macro em MAIÚSCULO e único
    GUARD_NAME="$(echo "${BASENAME}_MODEL_H" | tr '[:lower:]' '[:upper:]')"

    echo "▶ Convertendo $MODEL"

    # =========================
    # Gera o .cc temporário
    # =========================
    TMP_CC="$(mktemp)"
    xxd -i "$MODEL" > "$TMP_CC"

    # =========================
    # Cria o .cc final com include
    # =========================
    {
        echo "#include \"${HEADER_NAME}\""
        echo
        cat "$TMP_CC"
    } > "$CC_FILE"

    rm "$TMP_CC"

    # =========================
    # Ajusta símbolos e alinhamento
    # =========================
    sed -i "s/unsigned char .*\\[\\]/alignas(16) const unsigned char ${SYMBOL}[]/g" "$CC_FILE"
    sed -i "s/unsigned int .*_len/const unsigned int ${SYMBOL}_len/g" "$CC_FILE"

    # =========================
    # Header com include guard clássico
    # =========================
    cat > "$H_FILE" <<EOF
#ifndef ${GUARD_NAME}
#define ${GUARD_NAME}

extern const unsigned char ${SYMBOL}[];
extern const unsigned int ${SYMBOL}_len;

#endif /* ${GUARD_NAME} */
EOF

    echo "✔ Gerado:"
    echo "  $CC_FILE"
    echo "  $H_FILE"
    echo
done

echo "✅ Conversão concluída com sucesso!"
