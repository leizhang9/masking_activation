library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity uart2wb_fpga_tb is
end entity;

architecture arch of uart2wb_fpga_tb is

  constant clk_period : time := 10 ns;
  constant uart_clk_period : time := 1120 ns;

  signal clk            : std_logic := '0';
  signal uart_clk       : std_logic := '0';
  signal rst            : std_logic;
  signal ctrl_ack       : std_logic;
  signal ctrl_reg       : std_logic_vector(31 downto 0);
  signal gp_mem_reg     : std_logic_vector(32 * 16 - 1 downto 0);
  signal bram_data_o    : std_logic_vector(31 downto 0);
  signal bram_addr_o    : std_logic_vector(31 downto 0);
  signal bram_re        : std_logic;
  signal bram_we        : std_logic;
  signal bram_data_i    : std_logic_vector(31 downto 0);
  signal bram_index     : std_logic_vector(3 downto 0);
  signal brams_busy     : std_logic;
  signal status_mem_reg : std_logic_vector(32 * 16 - 1 downto 0);
  signal uart_rx        : std_logic := '1';
  signal uart_tx        : std_logic;

  procedure tx_byte_p (constant byte : in  std_ulogic_vector(7 downto 0);
                     signal uart_rxd_o : out std_ulogic) is
      variable i : integer;
  begin
      report "start tx_byte_p" severity note;

      wait until rising_edge(uart_clk);
      --start bit 0
      uart_rxd_o <= '0';
      wait until rising_edge(uart_clk);
      --data bits
      for i in 0 to 7 loop
        uart_rxd_o <= byte(i);
        wait until rising_edge(uart_clk);
      end loop;
      --parity even
      uart_rxd_o <= byte(7) xor byte(6) xor byte(5) xor byte(4) xor
                     byte(3) xor byte(2) xor byte(1) xor byte(0);
      wait until rising_edge(uart_clk);
      --stop bit 1
      uart_rxd_o <= '1';
      wait until rising_edge(uart_clk);

      report "end tx_byte_p" severity note;
  end tx_byte_p;

begin

  dut : entity work.UART2WB_FPGA_INTF(RTL)
  port map (
    CLK_i            => clk,
    RST_BTN_N        => rst,
    -- CTRL INTERFACE
    ctrl_ack_i       => ctrl_ack,
    ctrl_reg_o       => ctrl_reg,
    -- GP MEM INTERFACE
    gp_mem_reg_o     => gp_mem_reg,
    -- BRAM INTERFACE
    bram_data_o      => bram_data_o,
    bram_addr_o      => bram_addr_o,
    bram_re_o        => bram_re,
    bram_we_o        => bram_we,
    bram_data_i      => bram_data_i,
    bram_index_o     => bram_index,
    brams_busy_i     => brams_busy,
    -- STATUS INTERFACE
    status_mem_reg_i => status_mem_reg,
    -- UART INTERFACE
    UART_RXD         => uart_rx,
    UART_TXD         => uart_tx
  );

  clk <= not clk after clk_period / 2;
  uart_clk <= not uart_clk after uart_clk_period / 2;

  stim : process
  begin
    rst <= '0';
    wait for 10 * uart_clk_period;
    rst <= '1';
    wait for 10 * clk_period;

    tx_byte_p(x"03", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    tx_byte_p(x"00", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    tx_byte_p(x"00", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    tx_byte_p(x"00", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    tx_byte_p(x"40", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    tx_byte_p(x"02", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    for i in 0 to (2 * 4) - 1 loop
      tx_byte_p(std_ulogic_vector(to_unsigned(i, 8)), uart_rxd_o => uart_rx);
      wait for uart_clk_period;
    end loop;
    
    
    tx_byte_p(x"03", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    tx_byte_p(x"00", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    tx_byte_p(x"00", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    tx_byte_p(x"00", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    tx_byte_p(x"50", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    tx_byte_p(x"02", uart_rxd_o => uart_rx);
    wait for uart_clk_period;
    for i in 0 to (2 * 4) - 1 loop
      tx_byte_p(std_ulogic_vector(to_unsigned(i, 8)), uart_rxd_o => uart_rx);
      wait for uart_clk_period;
    end loop;



    wait for 10*uart_clk_period;

    report "SIMULATION FINSIHED" severity failure;

  end process;

end architecture;
