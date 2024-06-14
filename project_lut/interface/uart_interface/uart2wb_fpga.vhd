--------------------------------------------------------------------------------
-- PROJECT: SIMPLE UART FOR FPGA
--------------------------------------------------------------------------------
-- AUTHORS: Jakub Cabal <jakubcabal@gmail.com>
--			Matthias Glaser <matthias.glaser@tum.de>
-- LICENSE: The MIT License, please read LICENSE file
-- WEBSITE: https://github.com/jakubcabal/uart-for-fpga
--------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

-- MEMORY MODULE OF UART 2 WISHBONE
-- =======================================================

entity UART2WB_FPGA_INTF is
	Generic (
		status_mem_size_g   : positive := 16; -- number of 32 bit words
		gp_mem_size_g       : positive := 16; -- number of 32 bit words
		design_revision_g   : natural  := 16#00000000# -- design revision
	);
	Port (
		CLK_i            : in  std_logic; -- system clock
		RST_BTN_N        : in  std_logic; 
		-- CTRL INTERFACE
		ctrl_ack_i       : in  std_logic;
		ctrl_reg_o       : out std_logic_vector(31 downto 0);
		-- GP MEM INTERFACE
		gp_mem_reg_o     : out std_logic_vector(32 * gp_mem_size_g - 1 downto 0);
		-- BRAM INTERFACE
		bram_data_o           : out std_logic_vector(32 - 1 downto 0);
		bram_addr_o           : out std_logic_vector(32 - 1 downto 0);
		bram_re_o             : out std_logic;
		bram_we_o             : out std_logic;
		bram_data_i           : in  std_logic_vector(32 - 1 downto 0);
		bram_index_o          : out std_logic_vector(3 downto 0);
		brams_busy_i          : in  std_logic;
		-- STATUS INTERFACE
		status_mem_reg_i : in  std_logic_vector(32 * status_mem_size_g - 1 downto 0);
		-- UART INTERFACE
		UART_RXD         : in  std_logic;
		UART_TXD         : out std_logic
	);
end entity;

architecture RTL of UART2WB_FPGA_INTF is

	constant smallest_status_address_c : natural := 16#10000000#;
	constant ctrl_reg_address_c        : natural := 16#20000000#;
	constant design_revision_address_c : natural := 16#30000000#;
	constant smallest_gp_mem_address_c : natural := 16#40000000#;
	constant smallest_bram_address_c   : natural := 16#50000000#;


	signal rst_btn       : std_logic;
	signal reset         : std_logic;

	signal wb_cyc        : std_logic;
	signal wb_stb        : std_logic;
	signal wb_we         : std_logic;
	signal wb_addr       : std_logic_vector(31 downto 0);
	signal wb_dout       : std_logic_vector(31 downto 0);
	signal wb_stall      : std_logic;
	signal wb_ack        : std_logic;
	signal wb_din        : std_logic_vector(31 downto 0);

	signal mem_reg_sel : std_logic;
	signal mem_reg_we  : std_logic;

	signal status_mem_reg : std_logic_vector(32 * status_mem_size_g - 1 downto 0);

	signal gp_reg_sel : std_logic;
	signal gp_reg_we  : std_logic;
	signal gp_reg     : std_logic_vector(32 * gp_mem_size_g - 1 downto 0);

	signal ctrl_reg_sel : std_logic;
	signal ctrl_reg_we  : std_logic;
	signal ctrl_reg     : std_logic_vector(31 downto 0);


	type state_t is (
		IDLE_e,
		MEMORY_READ_e,
		MEMORY_WRITE_e,
		STATUS_READ_e,
		GP_MEM_WRITE_e,
		GP_MEM_READ_e,
		CTRL_READ_e,
		CTRL_WRITE_e,
		REVISION_READ_e,
		INTERNAL_ACCESS_e,
		INVALID_e
	);

	signal wb_state_reg : state_t;

begin

	rst_btn <= not RST_BTN_N;
	--rst_btn <= RST_BTN_N;

	rst_sync_i : entity work.RST_SYNC
	port map (
		CLK        => CLK_i,
		ASYNC_RST  => rst_btn,
		SYNCED_RST => reset
	);

	uart2wbm_i : entity work.UART2WBM
	generic map (
		CLK_FREQ  => 100000000,
		BAUD_RATE => 921600
	)
	port map (
		CLK      => CLK_i,
		RST      => reset,
		-- UART INTERFACE
		UART_TXD => UART_TXD,
		UART_RXD => UART_RXD,
		-- WISHBONE MASTER INTERFACE
		WB_CYC   => wb_cyc,
		WB_STB   => wb_stb,
		WB_WE    => wb_we,
		WB_ADDR  => wb_addr,
		WB_DOUT  => wb_din,
		WB_STALL => wb_stall,
		WB_ACK   => wb_ack,
		WB_DIN   => wb_dout
	);

 
	mem_reg_sel <= '1' when ((unsigned(wb_addr)) >= smallest_bram_address_c) else '0';
	mem_reg_we  <= wb_stb and wb_we and mem_reg_sel;
	
	ctrl_reg_sel <= '1' when ((unsigned(wb_addr)) = ctrl_reg_address_c) else '0';
	ctrl_reg_we  <= wb_stb and wb_we and ctrl_reg_sel;

	gp_reg_sel <= '1' when ((unsigned(wb_addr)) <  (smallest_gp_mem_address_c + gp_mem_size_g) and 
					(unsigned(wb_addr)) >= smallest_gp_mem_address_c) else '0';
	gp_reg_we  <= wb_stb and wb_we and gp_reg_sel;
	
	ctrl_reg_p : process (CLK_i)
	begin
		if (rising_edge(CLK_i)) then
			if (wb_state_reg = CTRL_WRITE_e) then
				ctrl_reg <= wb_din;
			elsif (ctrl_ack_i = '1') then
				ctrl_reg <= (others => '0');
			end if;
		end if;
	end process;

	ctrl_reg_o <= ctrl_reg;

	gp_reg_p : process (CLK_i)
	begin
		if (rising_edge(CLK_i)) then
			if (wb_state_reg = GP_MEM_WRITE_e) then
				gp_reg(
					(to_integer(unsigned(wb_addr(27 downto 0))) + 1) * 32 - 1 downto 
					to_integer(unsigned(wb_addr(27 downto 0))) * 32
				) <= wb_din;
			end if;
		end if;
	end process;

	gp_mem_reg_o <= gp_reg;

	wb_stall <= '1' when (brams_busy_i = '1') else '0'; -- stall master when internal memory access

	wb_ack_reg_p : process (CLK_i)
	begin
		if (rising_edge(CLK_i)) then
			if (brams_busy_i = '1') then
				-- internal memory access, do not send an ack
				wb_ack <= '0';
			else 
				wb_ack <= wb_cyc and wb_stb;
			end if;
		end if;
	end process;


	wb_state_reg_p : process (CLK_i, rst_btn)
	begin
		if rising_edge(CLK_i) then
			if rst_btn = '1' then
				wb_state_reg <= IDLE_e;
			elsif (unsigned(wb_addr)) >= smallest_bram_address_c then
				-- access memory
				if brams_busy_i = '1' then
					-- internal memory access - block uart access
					wb_state_reg <= INTERNAL_ACCESS_e;
				elsif mem_reg_we = '1' then
					wb_state_reg <= MEMORY_WRITE_e;
				else
					wb_state_reg <= MEMORY_READ_e;
				end if;
			elsif 
				(unsigned(wb_addr)) <  (smallest_status_address_c + status_mem_size_g) and 
				(unsigned(wb_addr)) >= smallest_status_address_c then

				-- access status memory
				wb_state_reg <= STATUS_READ_e;

			elsif 
				(to_integer(unsigned(wb_addr))) <  (smallest_gp_mem_address_c + gp_mem_size_g) and 
				(to_integer(unsigned(wb_addr))) >= smallest_gp_mem_address_c then

				-- access general purpose mem register
				if gp_reg_we = '1' then
					wb_state_reg <= GP_MEM_WRITE_e;
				else
					wb_state_reg <= GP_MEM_READ_e;
				end if;

			elsif 
				(unsigned(wb_addr)) = ctrl_reg_address_c then

				-- access ctrl register
				if ctrl_reg_we = '1' then
					wb_state_reg <= CTRL_WRITE_e;
				else
					wb_state_reg <= CTRL_READ_e;
				end if;
			elsif 
				(unsigned(wb_addr)) = design_revision_address_c then

				-- access design revision 
				wb_state_reg <= REVISION_READ_e;
			else
				wb_state_reg <= INVALID_e;
			end if;	

		end if;
	end process;

	wb_dout <=  bram_data_i when wb_state_reg = MEMORY_READ_e else
				gp_reg(
					(to_integer(unsigned(wb_addr(27 downto 0))) + 1) * 32 - 1 downto 
					to_integer(unsigned(wb_addr(27 downto 0))) * 32
				) when wb_state_reg = GP_MEM_READ_e and (to_integer(unsigned(wb_addr))) <  (smallest_gp_mem_address_c + gp_mem_size_g) else
				status_mem_reg(
					(to_integer(unsigned(wb_addr(27 downto 0))) + 1) * 32 - 1 downto 
					to_integer(unsigned(wb_addr(27 downto 0))) * 32
				) when wb_state_reg = STATUS_READ_e and to_integer(unsigned(wb_addr)) < (smallest_status_address_c + status_mem_size_g) else
				ctrl_reg when wb_state_reg = CTRL_READ_e else
				std_logic_vector(to_unsigned(design_revision_g, 32)) when wb_state_reg = REVISION_READ_e else
				X"EEEEEEEE" when wb_state_reg = INTERNAL_ACCESS_e else
				X"DEADCAFE" when wb_state_reg = INVALID_e else
				(others => '0');
	
	bram_data_o <= wb_din;
	bram_addr_o <= "0000" & wb_addr(27 downto 0) when wb_state_reg = MEMORY_READ_e or wb_state_reg = MEMORY_WRITE_e else (others => '0');
	bram_we_o <= '1' when wb_state_reg = MEMORY_WRITE_e else '0';
	bram_re_o <= '1' when wb_state_reg = MEMORY_READ_e else '0';
	bram_index_o <= wb_addr(31 downto 28) when wb_state_reg = MEMORY_READ_e or wb_state_reg = MEMORY_WRITE_e else (others => '0'); 


	status_mem_reg <= status_mem_reg_i;


end architecture;
