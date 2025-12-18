import { getBased64File } from "@/util/extra-1/blob";
import { getItemsByVector } from "@/util/extra-1/cosmos";
import { getChatCompletions, getEmbedding } from "@/util/extra-1/openai-extra-shrkm";
import { NextRequest, NextResponse } from "next/server";

export const POST = async (request: NextRequest) => {
    try {
        const { message } = await request.json();

        // 1. Get embedding for the input message
        const embedding = await getEmbedding(message);

        // 2. Retrieve relevant items from Cosmos DB based on the embedding
        const items = await getItemsByVector(embedding);

        // 3. Prepare images if any
        const images: string[] = [];
        for (const item of items) {
            if (item.is_contain_image && item.image_blob_path) {
                const base64Image = await getBased64File(item.image_blob_path);
                images.push(base64Image);
            }
        }

        // 4. Create system message with context from retrieved items
        let systemMessage = "'検索結果'と画像の情報のみを使って回答してください。分からない場合は「分かりません」と回答してください。 入力文は以下の通りです。:\n";
        for (const item of items) {
            systemMessage += `File: ${item.file_name}\nContent: ${item.content}\n\n`;
        }

        // 5. Get chat completions from OpenAI
        const chatCompletions = await getChatCompletions(systemMessage, message, images);
        const aiMessage = chatCompletions[0]?.message?.content || "I'm sorry, I couldn't generate a response.";

        return NextResponse.json({ aiMessage });
    } catch (error) {
        return NextResponse.json({ error: 'Error processing the request.' }, { status: 500 });
    }
};

export const dynamic = 'force-dynamic';