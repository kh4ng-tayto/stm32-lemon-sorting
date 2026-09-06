/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2026 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include <stdio.h>
#include <string.h>

/* =========================
   HANDLE
========================= */

I2C_HandleTypeDef hi2c1;
TIM_HandleTypeDef htim2;
UART_HandleTypeDef huart1;

/* =========================
   VARIABLE
========================= */

#define QUEUE_SIZE 20

#define PRODUCT_NONE     0

#define LEMON_GOOD       1

#define LEMON_BAD        2

#define UART_CMD_LEMON_GOOD   '1'
#define UART_CMD_LEMON_BAD    '2'
#define UART_CMD_RESET_UPPER  'R'
#define UART_CMD_RESET_LOWER  'r'
#define UART_CMD_QUERY_UPPER  'Q'
#define UART_CMD_QUERY_LOWER  'q'
/* FIFO Queue */

uint8_t product_queue[QUEUE_SIZE];

volatile uint8_t head = 0;
volatile uint8_t tail = 0;

/* UART */

uint8_t rx_data = 0;
volatile uint8_t uart_cmd = 0;
volatile uint8_t uart_cmd_ready = 0;

/* IR */
/* IR1 (PB0) = cong vat chanh good -> Servo1
   IR2 (PB1) = cong vat   -> Servo2 */

#define IR1_PIN   GPIO_PIN_0
#define IR2_PIN   GPIO_PIN_1

uint8_t ir1_old = 1;
uint8_t ir1_now = 1;

uint8_t ir2_old = 1;
uint8_t ir2_now = 1;

/* Product dang xu ly */

uint8_t currentProduct = PRODUCT_NONE;

/* Counter */


uint32_t lemon_good  = 0;
uint32_t lemon_bad   = 0;
uint8_t reset_ack = 0;
/* State Machine */

typedef enum
{
    STATE_IDLE = 0,
    STATE_DELAY,
    STATE_OPEN,
    STATE_WAIT,
    STATE_CLOSE

}State_t;

State_t state = STATE_IDLE;

uint32_t stateTick = 0;

/* =========================
   ANTI REPEAT
========================= */

uint32_t ir1Tick = 0;
uint32_t ir2Tick = 0;

uint8_t uart_last = 0;

uint32_t uartTick = 0;

/* =========================
   FUNCTION
========================= */

void LCD_Init(void);
void LCD_SetCursor(uint8_t row,uint8_t col);
void LCD_Print(char *str);
void LCD_SendCommand(uint8_t cmd);
void LCD_SendData(uint8_t data);
void I2C_Scanner(void);

void Servo1_Open(void);
void Servo1_Close(void);

void Servo2_Open(void);
void Servo2_Close(void);

void Queue_Push(uint8_t data);

uint8_t Queue_Pop(void);
uint8_t Queue_Peek(void);
uint8_t Queue_IsEmpty(void);
uint8_t Queue_IsFull(void);

void Process_Product(uint8_t type);
void LCD_Update(void);

void Queue_Push(uint8_t data)
{
    uint8_t next = (tail + 1) % QUEUE_SIZE;

    if(next != head)
    {
        product_queue[tail] = data;
        tail = next;
    }
}

uint8_t Queue_Pop(void)
{
    if(head == tail)
        return PRODUCT_NONE;

    uint8_t data = product_queue[head];

    head = (head + 1) % QUEUE_SIZE;

    return data;
}

uint8_t Queue_Peek(void)
{
    
    if(head == tail)
        return PRODUCT_NONE;

    return product_queue[head];
}

uint8_t Queue_IsEmpty(void)
{
    return head == tail;
}

uint8_t Queue_IsFull(void)
{
    uint8_t next = (tail + 1) % QUEUE_SIZE;
    return next == head;
}

void SystemClock_Config(void);

static void MX_GPIO_Init(void);
static void MX_I2C1_Init(void);
static void MX_TIM2_Init(void);
static void MX_USART1_UART_Init(void);
void System_Reset(void);
void Sorting_ResetData(void);
void UART_ProcessCommand(uint8_t cmd);
/* =========================
   MAIN
========================= */

int main(void)
{
    HAL_Init();
    SystemClock_Config();
    MX_GPIO_Init();
    MX_I2C1_Init();
    MX_TIM2_Init();
    MX_USART1_UART_Init();

    HAL_TIM_PWM_Start(&htim2, TIM_CHANNEL_1);
    HAL_TIM_PWM_Start(&htim2, TIM_CHANNEL_2);

    Servo1_Close();
    Servo2_Close();

    HAL_Delay(200);
    I2C_Scanner();

    LCD_Init();
    LCD_SetCursor(0,0);
    LCD_Print("LEMON SORTING");
    HAL_Delay(2000);
    LCD_SendCommand(0x01);
    LCD_Update();

    HAL_UART_Receive_IT(&huart1, &rx_data, 1);

    // Biến watchdog
    uint32_t last_loop_time = HAL_GetTick();

    while(1)
    {
        /* Xu ly lenh UART ben ngoai callback ngat.
           Khong goi HAL_Delay, LCD/I2C hay UART transmit trong ngat. */
        if(uart_cmd_ready)
        {
            uint8_t cmd;

            __disable_irq();
            cmd = uart_cmd;
            uart_cmd_ready = 0;
            __enable_irq();

            UART_ProcessCommand(cmd);
        }

        // Watchdog: Nếu loop bị treo > 5s, reset hệ thống
        if(HAL_GetTick() - last_loop_time > 5000)
        {
            char msg[] = "WATCHDOG_RESET\n";
            HAL_UART_Transmit(&huart1, (uint8_t*)msg, strlen(msg), 100);
            System_Reset();
            last_loop_time = HAL_GetTick();
        }

        // Đọc IR
        ir1_now = HAL_GPIO_ReadPin(GPIOB, IR1_PIN);
        ir2_now = HAL_GPIO_ReadPin(GPIOB, IR2_PIN);

        // Xử lý State Machine
        if(state == STATE_IDLE && !Queue_IsEmpty())
        {
            uint8_t nextProduct = Queue_Peek();

            if(nextProduct == LEMON_GOOD)
            {
                if(ir1_old == 1 && ir1_now == 0 && HAL_GetTick() - ir1Tick > 300)
                {
                    ir1Tick = HAL_GetTick();
                    currentProduct = Queue_Pop();
                    stateTick = HAL_GetTick();
                    state = STATE_DELAY;
                }
            }
            else if(nextProduct == LEMON_BAD)
            {
                if(ir2_old == 1 && ir2_now == 0 && HAL_GetTick() - ir2Tick > 300)
                {
                    ir2Tick = HAL_GetTick();
                    currentProduct = Queue_Pop();
                    stateTick = HAL_GetTick();
                    state = STATE_DELAY;
                }
            }
        }

        ir1_old = ir1_now;
        ir2_old = ir2_now;

        // State Machine
        switch(state)
        {
            case STATE_IDLE:
                break;

            case STATE_DELAY:
                if(HAL_GetTick() - stateTick > 400)
                {
                    state = STATE_OPEN;
                }
                break;

            case STATE_OPEN:
                switch(currentProduct)
                {
                    case LEMON_GOOD:
                        Servo1_Open();
                        break;
                    case LEMON_BAD:
                        Servo2_Open();
                        break;
                    default:
                        state = STATE_IDLE;
                        break;
                }
                stateTick = HAL_GetTick();
                state = STATE_WAIT;
                break;

            case STATE_WAIT:
                if(HAL_GetTick() - stateTick > 400)
                {
                    state = STATE_CLOSE;
                }
                break;

            case STATE_CLOSE:
                switch(currentProduct)
                {
                    case LEMON_GOOD:
                        Servo1_Close();
                        lemon_good++;
                        break;
                    case LEMON_BAD:
                        Servo2_Close();
                        lemon_bad++;
                        break;
                }
                LCD_Update();
                currentProduct = PRODUCT_NONE;
                state = STATE_IDLE;
                break;
        }

        last_loop_time = HAL_GetTick();
    }
}

/* =========================
   UART
========================= */

/* Callback ngat chi luu 1 byte vua nhan va kich hoat nhan byte tiep theo.
   Moi xu ly nang nhu LCD, I2C, HAL_Delay va UART transmit duoc thuc hien
   trong while(1) de tranh treo STM32. */
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
    if(huart->Instance == USART1)
    {
        if(!uart_cmd_ready)
        {
            uart_cmd = rx_data;
            uart_cmd_ready = 1;
        }

        HAL_UART_Receive_IT(&huart1, &rx_data, 1);
    }
}

void UART_ProcessCommand(uint8_t cmd)
{
    /* Bo qua ky tu xuong dong do Serial Monitor/Python co the gui kem. */
    if(cmd == '\r' || cmd == '\n')
    {
        return;
    }

    /* Nhan ca R hoa va r thuong. */
    if(cmd == UART_CMD_RESET_UPPER || cmd == UART_CMD_RESET_LOWER)
    {
        Sorting_ResetData();

        char ack[] = "RESET_OK\r\n";
        HAL_UART_Transmit(&huart1, (uint8_t *)ack, strlen(ack), 100);
    }
    else if(cmd == UART_CMD_QUERY_UPPER || cmd == UART_CMD_QUERY_LOWER)
    {
        char buffer[64];
        uint8_t queue_count = (tail - head + QUEUE_SIZE) % QUEUE_SIZE;

        sprintf(buffer, "G:%lu B:%lu Q:%u\r\n",
                lemon_good, lemon_bad, queue_count);
        HAL_UART_Transmit(&huart1, (uint8_t *)buffer, strlen(buffer), 100);
    }
    else if(cmd == UART_CMD_LEMON_GOOD)
    {
        if(!Queue_IsFull())
        {
            Queue_Push(LEMON_GOOD);

            char ack[] = "G_OK\r\n";
            HAL_UART_Transmit(&huart1, (uint8_t *)ack, strlen(ack), 100);
        }
        else
        {
            char err[] = "QUEUE_FULL\r\n";
            HAL_UART_Transmit(&huart1, (uint8_t *)err, strlen(err), 100);
        }
    }
    else if(cmd == UART_CMD_LEMON_BAD)
    {
        if(!Queue_IsFull())
        {
            Queue_Push(LEMON_BAD);

            char ack[] = "B_OK\r\n";
            HAL_UART_Transmit(&huart1, (uint8_t *)ack, strlen(ack), 100);
        }
        else
        {
            char err[] = "QUEUE_FULL\r\n";
            HAL_UART_Transmit(&huart1, (uint8_t *)err, strlen(err), 100);
        }
    }
    else
    {
        char err[] = "UNKNOWN_CMD\r\n";
        HAL_UART_Transmit(&huart1, (uint8_t *)err, strlen(err), 100);
    }
}

/* =========================
   RESET SYSTEM
========================= */
void Sorting_ResetData(void)
{
    // Reset counters
    lemon_good = 0;
    lemon_bad = 0;

    // Xoa queue
    head = 0;
    tail = 0;

    // Reset state machine
    currentProduct = PRODUCT_NONE;
    state = STATE_IDLE;
    stateTick = 0;

    // Reset IR states va bo loc lap
    ir1_old = HAL_GPIO_ReadPin(GPIOB, IR1_PIN);
    ir1_now = ir1_old;
    ir2_old = HAL_GPIO_ReadPin(GPIOB, IR2_PIN);
    ir2_now = ir2_old;
    ir1Tick = HAL_GetTick();
    ir2Tick = HAL_GetTick();

    // Dong ca hai servo
    Servo1_Close();
    Servo2_Close();
    HAL_Delay(100);

    // Xoa va cap nhat LCD
    LCD_SendCommand(0x01);
    HAL_Delay(2);
    LCD_Update();
}

void System_Reset(void)
{
    /* Reset du lieu phan loai, khong DeInit UART de tranh mat ngat nhan. */
    Sorting_ResetData();

    char msg[] = "System Reset Complete!\r\n";
    HAL_UART_Transmit(&huart1, (uint8_t *)msg, strlen(msg), 100);
}

/* =========================
   SERVO
========================= */
    void Servo1_Open(void)
    {
        __HAL_TIM_SET_COMPARE(&htim2,TIM_CHANNEL_1,2000);
    }

    void Servo1_Close(void)
    {
        __HAL_TIM_SET_COMPARE(&htim2,TIM_CHANNEL_1,500);
    }

    void Servo2_Open(void)
    {
        __HAL_TIM_SET_COMPARE(&htim2,TIM_CHANNEL_2,2000);
    }

    void Servo2_Close(void)
    {
        __HAL_TIM_SET_COMPARE(&htim2,TIM_CHANNEL_2,500);
    }

/* =========================
   I2C SCANNER (debug)
   Quet bus I2C, in dia chi tim duoc qua UART1
   (mo Serial Monitor, baud 9600 de xem)
========================= */
void I2C_Scanner(void)
{
    char msg[48];
    uint8_t found = 0;

    sprintf(msg, "\r\n--- I2C Scan start ---\r\n");
    HAL_UART_Transmit(&huart1, (uint8_t*)msg, strlen(msg), 100);

    for(uint8_t addr = 1; addr < 128; addr++)
    {
        if(HAL_I2C_IsDeviceReady(&hi2c1, (uint16_t)(addr << 1), 2, 10) == HAL_OK)
        {
            found = 1;
            sprintf(msg, "Found device at 0x%02X\r\n", addr);
            HAL_UART_Transmit(&huart1, (uint8_t*)msg, strlen(msg), 100);
        }
    }

    if(!found)
    {
        sprintf(msg, "No I2C device found! Check wiring/power.\r\n");
        HAL_UART_Transmit(&huart1, (uint8_t*)msg, strlen(msg), 100);
    }

    sprintf(msg, "--- I2C Scan end ---\r\n");
    HAL_UART_Transmit(&huart1, (uint8_t*)msg, strlen(msg), 100);
}

/* =========================
   LCD (I2C - PCF8574 backpack, LCD1602)
   Neu module cua ban dung dia chi I2C khac 0x27,
   doi lai LCD_I2C_ADDR ben duoi (vd 0x3F << 1).
========================= */

#define LCD_I2C_ADDR   (0x27 << 1)
#define LCD_BACKLIGHT  0x08
#define LCD_EN         0x04
#define LCD_RS         0x01

static void LCD_I2C_Write4Bits(uint8_t nibble, uint8_t rs)
{
    uint8_t base = (nibble & 0xF0) | LCD_BACKLIGHT | (rs ? LCD_RS : 0x00);
    uint8_t withEN  = base | LCD_EN;
    uint8_t noEN    = base;

    /* Ghi rieng tung buoc, co cho on dinh giua moi buoc,
       thay vi gop chung 1 goi I2C - de tranh loi tren
       cac module PCF8574 nhay/thieu pull-up */
    HAL_I2C_Master_Transmit(&hi2c1, LCD_I2C_ADDR, &base,   1, 100);
    HAL_Delay(1);
    HAL_I2C_Master_Transmit(&hi2c1, LCD_I2C_ADDR, &withEN, 1, 100);
    HAL_Delay(1);
    HAL_I2C_Master_Transmit(&hi2c1, LCD_I2C_ADDR, &noEN,   1, 100);
    HAL_Delay(1);
}

void LCD_SendCommand(uint8_t cmd)
{
    LCD_I2C_Write4Bits(cmd & 0xF0, 0);
    LCD_I2C_Write4Bits((cmd << 4) & 0xF0, 0);
    HAL_Delay(1);
}

void LCD_SendData(uint8_t data)
{
    LCD_I2C_Write4Bits(data & 0xF0, 1);
    LCD_I2C_Write4Bits((data << 4) & 0xF0, 1);
    HAL_Delay(1);
}

void LCD_Init(void)
{
    HAL_Delay(50);

    /* Ep ve 8-bit mode truoc, theo dung datasheet HD44780 */
    LCD_I2C_Write4Bits(0x30, 0);
    HAL_Delay(5);
    LCD_I2C_Write4Bits(0x30, 0);
    HAL_Delay(5);
    LCD_I2C_Write4Bits(0x30, 0);
    HAL_Delay(5);

    /* Chuyen sang 4-bit mode */
    LCD_I2C_Write4Bits(0x20, 0);
    HAL_Delay(5);

    LCD_SendCommand(0x28); /* 4-bit, 2 dong, font 5x8 */
    LCD_SendCommand(0x08); /* tat display */
    LCD_SendCommand(0x01); /* xoa man hinh */
    HAL_Delay(5);
    LCD_SendCommand(0x06); /* entry mode: tang con tro */
    LCD_SendCommand(0x0C); /* bat display, tat con tro/blink */
    HAL_Delay(5);
}

void LCD_SetCursor(uint8_t row, uint8_t col)
{
    uint8_t addr;

    switch(row)
    {
        case 0:  addr = 0x80 + col; break;
        case 1:  addr = 0xC0 + col; break;
        default: addr = 0x80 + col; break;
    }

    LCD_SendCommand(addr);
}

void LCD_Print(char *str)
{
    while(*str)
    {
        LCD_SendData((uint8_t)*str++);
    }
}

/* =========================
   LCD UPDATE
========================= */
void LCD_Update(void)
{
    char buf[17];

    // Xóa màn hình
    LCD_SendCommand(0x01);
    HAL_Delay(2);

    // Dòng 1: Lemon Good
    LCD_SetCursor(0, 0);
    sprintf(buf, "Lemon Good:%3lu  ", lemon_good);
    LCD_Print(buf);

    // Dòng 2: Lemon Bad
    LCD_SetCursor(1, 0);
    sprintf(buf, "Lemon Bad :%3lu  ", lemon_bad);
    LCD_Print(buf);


}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_NONE;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_HSI;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV1;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_0) != HAL_OK)
  {
    Error_Handler();
  }
}

/**
  * @brief I2C1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_I2C1_Init(void)
{

  /* USER CODE BEGIN I2C1_Init 0 */

  /* USER CODE END I2C1_Init 0 */

  /* USER CODE BEGIN I2C1_Init 1 */

  /* USER CODE END I2C1_Init 1 */
  hi2c1.Instance = I2C1;
  hi2c1.Init.ClockSpeed = 100000;
  hi2c1.Init.DutyCycle = I2C_DUTYCYCLE_2;
  hi2c1.Init.OwnAddress1 = 0;
  hi2c1.Init.AddressingMode = I2C_ADDRESSINGMODE_7BIT;
  hi2c1.Init.DualAddressMode = I2C_DUALADDRESS_DISABLE;
  hi2c1.Init.OwnAddress2 = 0;
  hi2c1.Init.GeneralCallMode = I2C_GENERALCALL_DISABLE;
  hi2c1.Init.NoStretchMode = I2C_NOSTRETCH_DISABLE;
  if (HAL_I2C_Init(&hi2c1) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN I2C1_Init 2 */

  /* USER CODE END I2C1_Init 2 */

}

/**
  * @brief TIM2 Initialization Function
  * @param None
  * @retval None
  */
static void MX_TIM2_Init(void)
{

  /* USER CODE BEGIN TIM2_Init 0 */

  /* USER CODE END TIM2_Init 0 */

  TIM_ClockConfigTypeDef sClockSourceConfig = {0};
  TIM_MasterConfigTypeDef sMasterConfig = {0};
  TIM_OC_InitTypeDef sConfigOC = {0};

  /* USER CODE BEGIN TIM2_Init 1 */

  /* USER CODE END TIM2_Init 1 */
  htim2.Instance = TIM2;
  htim2.Init.Prescaler = 7;
  htim2.Init.CounterMode = TIM_COUNTERMODE_UP;
  htim2.Init.Period = 19999;
  htim2.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
  htim2.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_ENABLE;
  if (HAL_TIM_Base_Init(&htim2) != HAL_OK)
  {
    Error_Handler();
  }
  sClockSourceConfig.ClockSource = TIM_CLOCKSOURCE_INTERNAL;
  if (HAL_TIM_ConfigClockSource(&htim2, &sClockSourceConfig) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_TIM_PWM_Init(&htim2) != HAL_OK)
  {
    Error_Handler();
  }
  sMasterConfig.MasterOutputTrigger = TIM_TRGO_RESET;
  sMasterConfig.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
  if (HAL_TIMEx_MasterConfigSynchronization(&htim2, &sMasterConfig) != HAL_OK)
  {
    Error_Handler();
  }
  sConfigOC.OCMode = TIM_OCMODE_PWM1;
  sConfigOC.Pulse = 1500;
  sConfigOC.OCPolarity = TIM_OCPOLARITY_HIGH;
  sConfigOC.OCFastMode = TIM_OCFAST_DISABLE;
  if (HAL_TIM_PWM_ConfigChannel(&htim2, &sConfigOC, TIM_CHANNEL_1) != HAL_OK)
  {
    Error_Handler();
  }
  sConfigOC.Pulse = 0;
  if (HAL_TIM_PWM_ConfigChannel(&htim2, &sConfigOC, TIM_CHANNEL_2) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN TIM2_Init 2 */

  /* USER CODE END TIM2_Init 2 */
  HAL_TIM_MspPostInit(&htim2);

}

/**
  * @brief USART1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_USART1_UART_Init(void)
{

  /* USER CODE BEGIN USART1_Init 0 */

  /* USER CODE END USART1_Init 0 */

  /* USER CODE BEGIN USART1_Init 1 */

  /* USER CODE END USART1_Init 1 */
  huart1.Instance = USART1;
  huart1.Init.BaudRate = 9600;
  huart1.Init.WordLength = UART_WORDLENGTH_8B;
  huart1.Init.StopBits = UART_STOPBITS_1;
  huart1.Init.Parity = UART_PARITY_NONE;
  huart1.Init.Mode = UART_MODE_TX_RX;
  huart1.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart1.Init.OverSampling = UART_OVERSAMPLING_16;
  if (HAL_UART_Init(&huart1) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN USART1_Init 2 */

  /* USER CODE END USART1_Init 2 */

}

/**
  * @brief GPIO Initialization Function
  * @param None
  * @retval None
  */
static void MX_GPIO_Init(void)
{
  GPIO_InitTypeDef GPIO_InitStruct = {0};
  /* USER CODE BEGIN MX_GPIO_Init_1 */

  /* USER CODE END MX_GPIO_Init_1 */

  /* GPIO Ports Clock Enable */
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();

  /*Configure GPIO pins : PB0 PB1 */
  GPIO_InitStruct.Pin = GPIO_PIN_0|GPIO_PIN_1;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_PULLUP;
  HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

  /* USER CODE BEGIN MX_GPIO_Init_2 */

  /* USER CODE END MX_GPIO_Init_2 */
}

/* USER CODE BEGIN 4 */

/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}
#ifdef USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
