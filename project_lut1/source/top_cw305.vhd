library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;
use work.my_package.all;

entity top is
  generic (
    num_brams        : integer := 2;
    addr_width       : integer := 32;
    num_cycles       : integer := 32
  );
  port (
    clk         : in std_logic;
    rst         : in std_logic;
    uart_rx     : in std_logic;
    uart_tx     : out std_logic;
    led_idle    : out std_logic;
    trigger     : out std_logic
  ) ;
end top ;

architecture rtl of top is

    signal bram_index           : std_logic_vector(4 - 1 downto 0);
    signal int_bram_idx         : std_logic_vector(4 - 1 downto 0);
    signal bram_addr            : std_logic_vector(addr_width - 1 downto 0);
    signal bram_data_i          : std_logic_vector(32 - 1 downto 0);
    signal bram_re              : std_logic;
    signal bram_we              : std_logic;
    signal bram_data_o          : std_logic_vector(32 - 1 downto 0);
    signal start                : std_logic;
    signal brams_busy           : std_logic;

    signal ctrl_ack_i           : std_logic;
    signal ctrl_reg_o           : std_logic_vector(31 downto 0);
    signal gp_mem_reg_o         : std_logic_vector(32 * 16 - 1 downto 0);
    signal status_mem_reg_i     : std_logic_vector(32 * 16 - 1 downto 0);

    signal int_rst              : std_logic;
    
    signal done                 : std_logic;

    signal lut_x1                : std_logic_vector(K - 1 downto 0);
    signal lut_rnd              : std_logic_vector(K - 1 downto 0);
    signal lut_out              : std_logic_vector(K - 1 downto 0);
    signal lut_x1_reg            : std_logic_vector(K - 1 downto 0);
    signal lut_rnd_reg          : std_logic_vector(K - 1 downto 0);
    signal lut_out_reg          : std_logic_vector(K - 1 downto 0);

    signal cnt                  : unsigned(32 - 1 downto 0);
    signal cnt_en               : std_logic;

begin

    int_rst <=  not rst;  --rst for basys3, not rst for measurement
    lut_x1 <= gp_mem_reg_o(K - 1 downto 0);
    lut_rnd <= gp_mem_reg_o(K + 32 - 1 downto 32);
    status_mem_reg_i(K - 1 downto 0) <= lut_out_reg;

    reg : process(clk)
    begin
        if clk'event and clk = '1' then
            if int_rst = '1' then
                lut_x1_reg <= (others => '0');
                lut_rnd_reg <= (others => '0');
                lut_out_reg <= (others => '0');
            elsif start = '1' then 
                lut_x1_reg <= lut_x1;
                lut_rnd_reg <= lut_rnd;
                lut_out_reg <= lut_out;
            end if ;
        end if ;
    end process ; -- register

    counter : process(clk)
    begin
        if clk'event and clk = '1' then
            done <= '0';
            if int_rst = '1' then
                cnt <= (others => '0');
                cnt_en <= '0';
            elsif start = '1' then 
                cnt_en <= '1';
            elsif cnt_en = '1' then  
                if to_integer(cnt) >= num_cycles then
                    cnt <= (others => '0');
                    cnt_en <= '0';
                    done <= '1';
                else 
                    cnt <= cnt + 1;
                end if ;
            end if ;
        end if ;    
    end process ; -- counter

    trigger_p : process(clk)
    begin
        if clk'event and clk = '1' then
            if int_rst = '1' or done = '1' then
                trigger <= '0';
                led_idle <= '1';
                brams_busy <= '0';
            elsif start = '1' then
                trigger <= '1';
                led_idle <= '0';
                brams_busy <= '1';
            end if ;
        end if ;
    end process ; -- trigger_p

    start_dut : process(clk)
    begin
        if clk'event and clk = '1' then
        ctrl_ack_i <= '0';
        start <= '0';
            if to_integer(unsigned(ctrl_reg_o)) = 1 then
                start <= '1';
                ctrl_ack_i <= '1';
            end if;
        end if;
    end process;

    lut : entity work.masked_lut(dump)
    port map (
        x1 => lut_x1_reg,
        clk => clk,
        reset => int_rst,
        rnd => lut_rnd_reg,
        output => lut_out
    );

    wb : entity work.UART2WB_FPGA_INTF(RTL)
    port map (
        CLK_i            => clk,
        RST_BTN_N        => rst,  -- not int_rst for basys3, rst for measurement
        -- CTRL INTERFACE
        ctrl_ack_i       => ctrl_ack_i,
        ctrl_reg_o       => ctrl_reg_o,
        -- GP MEM INTERFACE
        gp_mem_reg_o     => gp_mem_reg_o,
        -- BRAM INTERFACE
        bram_data_o      => bram_data_i,
        bram_addr_o      => bram_addr,
        bram_re_o        => bram_re,
        bram_we_o        => bram_we,
        bram_data_i      => bram_data_o,
        bram_index_o     => bram_index,
        brams_busy_i     => brams_busy,
        -- STATUS INTERFACE
        status_mem_reg_i => status_mem_reg_i,
        -- UART INTERFACE
        UART_RXD         => uart_rx,
        UART_TXD         => uart_tx
    );

end architecture ; -- rtl
