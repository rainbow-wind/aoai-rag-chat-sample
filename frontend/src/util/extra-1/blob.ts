import { BlobServiceClient, StorageSharedKeyCredential } from '@azure/storage-blob';

export const getBased64File = async (file_path: string): Promise<string> => {
    return new Promise<string>(async (resolve, reject) => {
        const sharedKeyCredentials = new StorageSharedKeyCredential(
            process.env.AZURE_STORAGE_ACCOUNT_NAME || '',
            process.env.AZURE_STORAGE_ACCOUNT_ACCESS_KEY || ''
        );
        const blobServiceClient = new BlobServiceClient( 
            `https://${process.env.AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net`,
            sharedKeyCredentials
        );

        const containerClient = blobServiceClient.getContainerClient(
            process.env.AZURE_STORAGE_CONTAINER_NAME || ''
        );
        const blobClient = containerClient.getBlobClient(file_path);

        const downloadBlockBlobResponse = await blobClient.download(0);

        let encodedData = '';
        if(downloadBlockBlobResponse.readableStreamBody) {
            const downloaded = await streamToBuffer(downloadBlockBlobResponse.readableStreamBody);
            const strData = downloaded.toString('base64');
            resolve(strData);
        }else{
            reject('Failed to get blob data');
        };
    });
    
}

async function streamToBuffer(readableStream: NodeJS.ReadableStream): Promise<any> {
    return new Promise((resolve, reject) => {
        const chunks: any[] = [];
        readableStream.on('data', (data) => {
            chunks.push(data instanceof Buffer ? data : Buffer.from(data));
        })
        readableStream.on('end', () => {
            resolve(Buffer.concat(chunks));
        });
        readableStream.on('error', reject);
    });
};