import { createSlice } from '@reduxjs/toolkit';
import { RootState } from '../store/store';
import { MessageType } from '../types/type';
import { access } from 'fs';

type InitialStateType = {
    ragextra1: MessageType[];
};

const initialState: InitialStateType = {
    ragextra1: [],
};

export const messageSlice = createSlice({
    name: 'message',
    initialState,
    reducers: {
        inputMessageToReduxStore: (state, action) => {
            if (action.payload.pathname === '/') {
                state.ragextra1.push(action.payload);
            }
        },
    },
});

export const { inputMessageToReduxStore } = messageSlice.actions;
export const selectMessage = (state: RootState) => state.message;
export default messageSlice.reducer;