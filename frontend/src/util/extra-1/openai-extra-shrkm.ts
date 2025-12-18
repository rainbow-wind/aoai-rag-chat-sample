import { AzureKeyCredential, OpenAIClient } from "@azure/openai";

export const getChatCompletions = async (
    systemMessage: string,
    message: string,
    images: string[]
): Promise<any[]> => {
    return new Promise<any[]>(async (resolve, reject) => {
        const endpoint = process.env.AZURE_OPENAI_ENDPOINT || '';
        const apiKey = process.env.AZURE_OPENAI_API_KEY || '';
        const deploymentId = process.env.AZURE_OPENAI_DEPLOYMENT_ID || '';

        const client = new OpenAIClient(
            endpoint,
            new AzureKeyCredential(apiKey)
        );

        if(images.length > 0) {
            try {
                const chatCompletions = await client.getChatCompletions(
                    deploymentId, 
                    [
                        { role: "system", content: systemMessage },
                        { role: "user", content: message},
                        {
                            role: "user",
                            content: [
                                { type: "image_url", imageUrl: {
                                    url:`data:image/jpg;base64,${images[0]}`
                                }}
                            ]
                        }
                    ], 
                    { maxTokens: 4096 }
                );

                resolve(chatCompletions.choices);
            } catch (error) {
                reject(error);
            }
        } else {
            try {
                const chatCompletions = await client.getChatCompletions(
                    deploymentId, [
                        { role: "system", content: systemMessage },
                        { role: "user", content: message}
                ], 
                { maxTokens: 4096 });
                resolve(chatCompletions.choices);
            } catch (error: any) {
                reject(error);  
            }
        }
    } 
);};

export const getEmbedding = async (message: string): Promise<number[]> => {
    return new Promise(async (resolve, reject) => {
        const endpoint = process.env.AZURE_OPENAI_ENDPOINT || '';
        const apiKey = process.env.AZURE_OPENAI_API_KEY || '';
        const embeddingDeploymentId = process.env.AZURE_OPENAI_VEC_DEPLOYMENT_ID || '';

        const client = new OpenAIClient(
            endpoint,
            new AzureKeyCredential(apiKey)
        );

        try {
            const embeddingResponse = await client.getEmbeddings(
                embeddingDeploymentId,
                [message]
            );
            resolve(embeddingResponse.data[0].embedding);
        } catch (error) {
            reject(error);
        }
    });
};